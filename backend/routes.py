from flask import Blueprint, render_template, request, jsonify
from sqlalchemy.exc import IntegrityError
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from models import Event, Resource, Contact, Newsletter, db
from backend.MailIntegration import ProfessionalEmailSender
import threading
from datetime import datetime

# Import ChatBot with error handling
try:
    from backend.Chatbot import ChatBot
    CHATBOT_AVAILABLE = True
except ImportError as e:
    print(f"Chatbot import failed: {e}")
    CHATBOT_AVAILABLE = False

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)
admin_bp = Blueprint('admin', __name__)

# Initialize mail sender (lazy instantiate to avoid import issues)
email_sender = ProfessionalEmailSender()

# Main routes
@main_bp.route('/')
def index():
    return render_template('index-tailwind.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/events')
def events():
    events = Event.query.filter_by(status='upcoming').order_by(Event.date.asc()).all()
    return render_template('events.html', events=events)

@main_bp.route('/resources')
def resources():
    featured_resources = Resource.query.filter_by(is_featured=True).all()
    all_resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template('resources.html', 
                         featured_resources=featured_resources, 
                         all_resources=all_resources)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

# API Routes
@api_bp.route('/events', methods=['GET'])
def get_events():
    """Get all events"""
    events = Event.query.order_by(Event.date.asc()).all()
    return jsonify([event.to_dict() for event in events])

@api_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event"""
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())

@api_bp.route('/events', methods=['POST'])
def create_event():
    """Create new event"""
    data = request.get_json()
    
    event = Event(
        title=data['title'],
        description=data['description'],
        date=datetime.fromisoformat(data['date']),
        location=data['location'],
        attendees=data.get('attendees', 0),
        price=data.get('price', 'Free'),
        image_url=data.get('image_url'),
        status=data.get('status', 'upcoming')
    )
    
    db.session.add(event)
    db.session.commit()
    
    # Announce event to active newsletter subscribers in background
    def announce_event_async(new_event_id: int):
        try:
            new_event = Event.query.get(new_event_id)
            if not new_event:
                return
            subscribers = Newsletter.query.filter_by(is_active=True).all()
            for subscriber in subscribers:
                try:
                    email_sender.send_event_announcement(
                        recipient_email=subscriber.email,
                        event_title=new_event.title,
                        event_date=new_event.date.isoformat() if new_event.date else None,
                        location=new_event.location,
                        description=new_event.description
                    )
                except Exception as e:
                    print(f"Failed to send event email to {subscriber.email}: {e}")
        except Exception as e:
            print(f"Event announcement worker error: {e}")

    threading.Thread(target=announce_event_async, args=(event.id,), daemon=True).start()

    return jsonify(event.to_dict()), 201

@api_bp.route('/resources', methods=['GET'])
def get_resources():
    """Get all resources"""
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return jsonify([resource.to_dict() for resource in resources])

@api_bp.route('/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Get specific resource"""
    resource = Resource.query.get_or_404(resource_id)
    return jsonify(resource.to_dict())

@api_bp.route('/resources/<int:resource_id>/download', methods=['POST'])
def download_resource(resource_id):
    """Download resource and increment counter"""
    resource = Resource.query.get_or_404(resource_id)
    resource.download_count += 1
    db.session.commit()
    
    return jsonify({'message': 'Download recorded', 'download_count': resource.download_count})

@api_bp.route('/contact', methods=['POST'])
def submit_contact():
    """Submit contact form"""
    data = request.get_json()
    
    contact = Contact(
        name=data['name'],
        email=data['email'],
        subject=data['subject'],
        message=data['message'],
        phone=data.get('phone'),
        company=data.get('company')
    )
    
    db.session.add(contact)
    db.session.commit()
    
    return jsonify({'message': 'Contact form submitted successfully'}), 201

@api_bp.route('/newsletter', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    data = request.get_json()
    email = data['email']
    
    # Check if email already exists
    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        if existing.is_active:
            return jsonify({'message': 'Already subscribed'}), 200
        else:
            existing.is_active = True
            db.session.commit()
            # Send welcome email on resubscribe (background)
            threading.Thread(target=email_sender.send_welcome_email, args=(email,), daemon=True).start()
            return jsonify({'message': 'Resubscribed successfully'}), 200
    
    newsletter = Newsletter(email=email)
    db.session.add(newsletter)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Another request likely inserted concurrently; treat as idempotent success
        return jsonify({'message': 'Already subscribed'}), 200
    
    # Send welcome email in background
    threading.Thread(target=email_sender.send_welcome_email, args=(email,), daemon=True).start()
    
    return jsonify({'message': 'Successfully subscribed to newsletter'}), 201

@api_bp.route('/newsletter/<email>', methods=['DELETE'])
def unsubscribe_newsletter(email):
    """Unsubscribe from newsletter"""
    newsletter = Newsletter.query.filter_by(email=email).first()
    if newsletter:
        newsletter.is_active = False
        db.session.commit()
        return jsonify({'message': 'Successfully unsubscribed'})
    
    return jsonify({'message': 'Email not found'}), 404

@api_bp.route('/chatbot', methods=['POST'])
def chatbot_response():
    """Handle chatbot messages with session tracking"""
    if not CHATBOT_AVAILABLE:
        return jsonify({
            'error': 'Chatbot service is temporarily unavailable',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        bot_response = ChatBot(user_message, session_id)
        
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'error': 'Sorry, I encountered an error. Please try again.',
            'timestamp': datetime.now().isoformat()
        }), 500

# Admin routes
@admin_bp.route('/')
def admin_dashboard():
    """Admin dashboard"""
    events_count = Event.query.count()
    resources_count = Resource.query.count()
    contacts_count = Contact.query.count()
    newsletter_count = Newsletter.query.filter_by(is_active=True).count()
    
    recent_contacts = Contact.query.order_by(Contact.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         events_count=events_count,
                         resources_count=resources_count,
                         contacts_count=contacts_count,
                         newsletter_count=newsletter_count,
                         recent_contacts=recent_contacts)

@admin_bp.route('/events')
def admin_events():
    """Admin events management"""
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('admin/events.html', events=events)

@admin_bp.route('/resources')
def admin_resources():
    """Admin resources management"""
    resources = Resource.query.order_by(Resource.created_at.desc()).all()
    return render_template('admin/resources.html', resources=resources)

@admin_bp.route('/contacts')
def admin_contacts():
    """Admin contacts management"""
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin/contacts.html', contacts=contacts)

@admin_bp.route('/newsletter')
def admin_newsletter():
    """Admin newsletter management"""
    subscribers = Newsletter.query.filter_by(is_active=True).order_by(Newsletter.subscribed_at.desc()).all()
    return render_template('admin/newsletter.html', subscribers=subscribers)
