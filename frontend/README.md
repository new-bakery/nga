# Frontend

This is the frontend application built with React and Vite.

## Prerequisites

- Node.js (Latest LTS version recommended)
- npm (comes with Node.js)

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the variables as needed

3. Start the development server:
```bash
npm run dev
```

## Environment Variables

All environment variables must be prefixed with `VITE_` to be exposed to the frontend code.

```
# API Configuration
VITE_API_BASE_URL=http://localhost:8000    # Backend API URL

# App Configuration
VITE_APP_NAME="NGA Application"            # Application name
VITE_APP_VERSION="1.0.0"                  # Application version
```

## Project Structure

```
frontend/
├── data/           # Data files
├── public/         # Public assets
├── src/           # Source code
│   ├── components/ # React components
│   ├── pages/     # Page components
│   └── services/  # API services
├── index.html     # Entry HTML file
├── .env           # Environment variables
└── vite.config.js # Vite configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

## Development

This project uses:
- React for UI components
- Vite as the build tool and development server
- CSS for styling

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 