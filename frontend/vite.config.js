export default {
    server: {
      proxy: {
        '/api': 'http://127.0.0.1:5000'  // Flask server URL
      }
    }
  };
  