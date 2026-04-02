# Email Digest Summarizer - Frontend

A modern React application for managing email digest configurations and delivery channels.

## Features

- Create and manage email digest configurations
- Configure filters (Sender, Keyword)
- Set up delivery channels (WhatsApp, Telegram, Discord)
- Schedule digest runs
- Monitor digest history and execution status
- Gmail OAuth authentication
- Background scheduler management

## Tech Stack

- React 18
- Vite
- React Router v6
- CSS Modules
- Fetch API

## Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── Modal.jsx
│   │   ├── Modal.module.css
│   │   ├── Toast.jsx
│   │   ├── Toast.module.css
│   │   ├── ToggleSwitch.jsx
│   │   ├── ToggleSwitch.module.css
│   │   ├── StatusBadge.jsx
│   │   ├── Sidebar.jsx
│   │   └── Sidebar.module.css
│   ├── pages/                # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Dashboard.module.css
│   │   ├── DigestDetail.jsx
│   │   ├── DigestDetail.module.css
│   │   ├── Channels.jsx
│   │   ├── Channels.module.css
│   │   ├── History.jsx
│   │   ├── History.module.css
│   │   ├── Settings.jsx
│   │   └── Settings.module.css
│   ├── App.jsx               # Main app component
│   ├── App.css               # Global styles
│   ├── api.js                # API client
│   └── main.jsx              # React entry point
├── index.html                # HTML entry point
├── vite.config.js            # Vite configuration
├── package.json              # Dependencies
└── .gitignore
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

The frontend is configured to proxy API requests from `/api` to `http://localhost:8000` (the backend).

### Building

Create a production build:
```bash
npm run build
```

### Production Preview

Preview the production build:
```bash
npm run preview
```

## API Configuration

The frontend expects the backend to be running on `http://localhost:8000`. This is configured in `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### Supported API Endpoints

- `GET/POST /api/digests` - List/create digest configs
- `GET/PUT/DELETE /api/digests/{id}` - Single digest CRUD
- `POST /api/digests/{id}/run` - Manual run
- `GET/POST /api/digests/{id}/filters` - List/create filters
- `DELETE /api/filters/{id}` - Delete filter
- `GET/POST /api/digests/{id}/channels` - List/create channels
- `PUT/DELETE /api/channels/{id}` - Update/delete channel
- `GET /api/digests/{id}/history` - Get digest history
- `GET /api/gmail/auth-url` - Get OAuth URL
- `GET /api/gmail/callback` - OAuth callback
- `GET /api/gmail/status` - Check Gmail connection
- `GET /api/scheduler/status` - Scheduler status
- `POST /api/scheduler/start, /api/scheduler/stop` - Control scheduler

## Components

### Pages

- **Dashboard**: List all digests, create new, quick run, delete
- **DigestDetail**: Configure individual digest, manage filters/channels
- **Channels**: Overview of all configured channels with setup guides
- **History**: Full history of digest runs with filtering
- **Settings**: Gmail OAuth, scheduler control, environment info

### Reusable Components

- **Modal**: Dialog for forms and confirmations
- **Toast**: Notification system
- **ToggleSwitch**: Switch toggle for boolean values
- **StatusBadge**: Status indicators with color coding
- **Sidebar**: Navigation sidebar

## Styling

The application uses CSS Modules for component-specific styles and global CSS variables for theming.

### CSS Variables

Dark theme with customizable colors:
- `--color-bg-primary`: #0d1117
- `--color-text-primary`: #e6edf3
- `--color-accent`: #58a6ff
- `--color-success`: #3fb950
- `--color-danger`: #f85149

## Error Handling

All API calls include error handling with user-friendly toast notifications. Loading states are displayed while data is being fetched.

## Responsive Design

The application is fully responsive and works on:
- Desktop screens
- Tablets
- Mobile devices

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Future Enhancements

- Email preview functionality
- Advanced filtering options
- Digest templates
- Rate limiting configuration
- Webhook testing
- Export digest history
