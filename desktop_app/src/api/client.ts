import axios from 'axios';

const client = axios.create({
    baseURL: '/', // Vite proxy will handle the forwarding to localhost:8000
    headers: {
        'Content-Type': 'application/json',
    },
});

export default client;
