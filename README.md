# VBSDeSterrenboom

Odoo module for managing parent committee (oudercomité) activities for sterrenboom.

## Features

- **Member Management**: Track committee members with their roles (Chairman, Treasurer, Secretary, Member)
- **Event Management**: Create and manage committee events with attendee tracking
- **Built-in Communication**: Chatter functionality for discussions on members and events

## Module Structure

```
sterrenboom/
├── __init__.py           # Module initialization
├── __manifest__.py       # Module metadata and dependencies
├── models/
│   ├── __init__.py
│   └── sterrenboom_model.py  # Member and Event models
├── views/
│   └── sterrenboom_views.xml # Forms, trees, and menu items
└── security/
    └── ir.model.access.csv   # Access control rules
```

## Installation

1. **Clone or extract this module** into your Odoo `addons` directory:
   ```bash
   git clone https://github.com/DF-DataForge/VBSDeSterrenboom.git
   mv VBSDeSterrenboom sterrenboom
   ```

2. **Restart Odoo** (if using server mode) or **refresh** (in development mode)

3. **Install the module**:
   - Go to Apps → Search for "Sterrenboom"
   - Click "Install"

4. **Access the module**:
   - Menu: Sterrenboom → Members / Events
   - Or search for "Members" or "Events" in the search bar

## Models

### sterrenboom.member
Represents a committee member with the following fields:
- **Name**: Member's full name (required)
- **Email**: Email address (unique)
- **Phone**: Contact phone number
- **Role**: Position in committee (Chairman, Treasurer, Secretary, Member)
- **Active**: Toggle to deactivate members

### sterrenboom.event
Represents a committee event with the following fields:
- **Event Name**: Name of the event (required)
- **Event Date**: When the event takes place (required)
- **Location**: Where the event is held
- **Description**: Event details
- **Attendees**: Link to member records attending the event
- **State**: Event status (Planned, Ongoing, Completed, Cancelled)
- **Notes**: Additional notes about the event

## Usage

### Adding a Member
1. Go to Sterrenboom → Members
2. Click "Create"
3. Fill in name, email, phone, and role
4. Save

### Creating an Event
1. Go to Sterrenboom → Events
2. Click "Create"
3. Enter event name and date
4. Add location, description, and attendees
5. Set event state
6. Save

## Development

To extend this module:

- Add new models in `models/sterrenboom_model.py`
- Create corresponding views in `views/sterrenboom_views.xml`
- Update `models/__init__.py` to import new models
- Add access rules in `security/ir.model.access.csv`

## License

LGPL-3

## Author

Data Forge - https://github.com/DF-DataForge
