// api/login.js
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

  try {
    console.log(`Proxying login request`);
    console.log('Request body:', req.body);
    
    // Forward the request to your AWS backend - notice we use the explicit path
    const backendResponse = await axios({
      method: 'POST',
      url: 'http://54.86.99.85:5000/api/login',  // Full explicit path
      data: req.body,
      headers: {
        'Content-Type': req.headers['content-type'] || 'application/json',
      }
    });

    console.log('Backend login response status:', backendResponse.status);
    
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