# Quick Start Guide

## Installation & Setup (2 minutes)

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm run dev

# 3. Open in browser
# http://localhost:5173
```

## What to Do First

### 1. Connect Gmail
- Go to Settings
- Click "Connect Gmail"
- Authorize with your Google account
- You'll be redirected back to the app

### 2. Start the Scheduler
- Stay on Settings
- Click "Start Scheduler" to enable automatic digest runs
- Status will show "Running"

### 3. Create Your First Digest
- Go to Dashboard
- Click "+ New Digest"
- Enter name, description, and schedule time
- Click Create

### 4. Configure Filters (Optional)
- Click "Configure" on your new digest
- Go to Filters section
- Add filters by sender or keyword
- Save

### 5. Add Delivery Channels
- On the same page, go to Channels section
- Click "+ Add Channel"
- Choose type (WhatsApp, Telegram, or Discord)
- Enter required credentials:
  - **WhatsApp**: Phone number (e.g., +1234567890)
  - **Telegram**: Chat ID (get from your bot)
  - **Discord**: Webhook URL (from server settings)
- Set as Primary if desired
- Click Add

### 6. Run Your First Digest
- Click "Run Now" button
- Go to History to monitor execution
- Check the expandable details for results

## Key Pages

| Page | Purpose | Actions |
|------|---------|---------|
| Dashboard | List all digests | Create, Edit, Delete, Run |
| Digest Detail | Configure one digest | Edit settings, manage filters, manage channels |
| Channels | View all channels | See setup guides for each platform |
| History | Monitor past runs | Filter by digest, view execution details |
| Settings | System configuration | Gmail auth, scheduler control, environment info |

## Useful Tips

- Use filters to narrow down which emails get included
- Set filters by sender email or keywords in subject/body
- You can have multiple channels and set one as primary
- Schedule time uses 24-hour format (09:00 = 9 AM)
- History shows last 5 runs on detail page
- Use Toast notifications to confirm actions

## API Connection

The app automatically proxies API requests to `http://localhost:8000`

Make sure your backend is running before starting the frontend.

## Troubleshooting

### "Cannot connect to API"
- Ensure backend is running on http://localhost:8000
- Check network tab in browser DevTools for blocked requests

### "Gmail connection failed"
- Make sure you have OAuth credentials configured on the backend
- Check that GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are set

### "No channels available"
- You must add at least one channel to a digest
- Phone number/chat ID/webhook URL must be valid

### Styles look broken
- Clear browser cache (Ctrl+Shift+Delete)
- Hard refresh (Ctrl+Shift+R)
- Restart dev server (npm run dev)

## File Editing

Key files to know about:

- `src/api.js` - Backend API calls (change base URL here if needed)
- `src/App.css` - Global theme colors and variables
- `src/pages/` - Each page of the app
- `src/components/` - Reusable UI components
- `vite.config.js` - Build config (API proxy here)

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview

# Deploy the 'dist' folder to your hosting
```

## Support

For issues or questions:
1. Check the README.md for full documentation
2. Review the FRONTEND_SUMMARY.md for architecture
3. Check browser console for error messages
4. Verify backend is running and accessible

Happy digesting! 📧
