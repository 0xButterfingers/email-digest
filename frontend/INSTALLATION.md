# Installation Instructions

## Prerequisites

- Node.js 16.0.0 or higher
- npm 7.0.0 or higher
- Backend running on http://localhost:8000 (optional for initial setup)

## Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

## Step 2: Install Dependencies

```bash
npm install
```

This will install:
- React 18.2.0
- React Router DOM 6.20.0
- Vite 5.0.8
- Supporting packages

Expected time: 30-60 seconds

## Step 3: Start Development Server

```bash
npm run dev
```

Output should show:
```
VITE v5.0.8  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

## Step 4: Open Application

Open your browser and navigate to:
```
http://localhost:5173
```

You should see:
- Dark-themed application
- Navigation sidebar with 4 options
- Main header "📧 Email Digest Summarizer"
- Empty dashboard message

## Step 5: Connect Backend

The frontend is configured to proxy API calls to `http://localhost:8000`.

Ensure your backend is running, or you'll see API errors.

### To Start Backend (if available)
```bash
# In a separate terminal, from the backend directory
python main.py
# or
./run.sh
```

## Step 6: Test the Application

1. Go to **Settings** page
2. Click **"Connect Gmail"** to test OAuth
3. Go to **Dashboard** 
4. Click **"+ New Digest"** to test API

## Troubleshooting

### Port 5173 Already in Use
```bash
npm run dev -- --port 5174
```
Then navigate to http://localhost:5174

### Module Not Found Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### "Cannot connect to API"
- Check if backend is running on http://localhost:8000
- Check browser console for error messages (F12)
- Verify network request in DevTools

### Styles Not Loading
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Restart dev server

### White Screen
- Check browser console for JavaScript errors (F12)
- Try different browser
- Verify Node.js version: `node --version`

## Production Build

When ready to deploy:

```bash
# Build optimized production bundle
npm run build

# Output goes to 'dist/' folder
# Preview production build
npm run preview
```

Then deploy the `dist/` folder to your hosting provider.

## Available Scripts

| Script | Purpose |
|--------|---------|
| `npm run dev` | Start development server with HMR |
| `npm run build` | Create production build |
| `npm run preview` | Preview production build locally |

## Next Steps

1. Read the **QUICKSTART.md** for 2-minute setup
2. Review **README.md** for full documentation
3. Check **MANIFEST.md** for project structure

## Support

For issues:
1. Check the troubleshooting section above
2. Review browser console errors
3. Verify backend is accessible
4. Check that all dependencies installed correctly

Happy coding! 📧
