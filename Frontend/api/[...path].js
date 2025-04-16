// api/[...path].js
const axios = require('axios');

export default async function handler(req, res) {
  // Get the path from the request
  const { path } = req.query;
  
  try {
    // Forward the request to your AWS backend
    const backendResponse = await axios({
      method: req.method,
      url: `http://54.86.99.85:5000/api/${path.join('/')}`,
      data: req.body,
      headers: {
        ...req.headers,
        host: '54.86.99.85:5000'
      },
      // Handle query parameters
      params: req.query
    });

    // Return the response from your backend
    res.status(backendResponse.status).json(backendResponse.data);
  } catch (error) {
    console.error('Error proxying to backend:', error);
    res.status(error.response?.status || 500).json(error.response?.data || { message: 'Internal Server Error' });
  }
}