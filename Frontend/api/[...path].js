// api/[...path].js
const axios = require('axios');

export default async function handler(req, res) {
  // Enable CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization');

  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Get the path from the request
  let path = Array.isArray(req.query.path) ? req.query.path.join('/') : req.query.path;
  
  // Remove leading 'api/' if present (handles /api/api/something case)
  if (path.startsWith('api/')) {
    path = path.substring(4);
  }
  
  try {
    console.log(`Proxying ${req.method} request to: http://54.86.99.85:5000/api/${path}`);
    console.log('Request body:', req.body);
    
    // Forward the request to your AWS backend
    const backendResponse = await axios({
      method: req.method,
      url: `http://54.86.99.85:5000/api/${path}`,
      data: req.body,
      headers: {
        'Content-Type': req.headers['content-type'] || 'application/json',
      },
      params: Object.fromEntries(
        Object.entries(req.query).filter(([key]) => key !== 'path')
      )
    });

    console.log('Backend response status:', backendResponse.status);
    
    // Return the response from your backend
    res.status(backendResponse.status).json(backendResponse.data);
  } catch (error) {
    console.error('Error proxying to backend:', error.message);
    
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else if (error.request) {
      res.status(500).json({ message: 'Backend server not responding' });
    } else {
      res.status(500).json({ message: 'Error setting up request: ' + error.message });
    }
  }
}