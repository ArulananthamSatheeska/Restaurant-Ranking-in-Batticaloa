import axios from 'axios';

axios.get('/api/restaurants')  // Proxy to Flask backend
  .then(response => {
    console.log(response.data);
  })
  .catch(error => {
    console.error("There was an error fetching the data!", error);
  });
