import axios from 'axios';

const client = axios.create({
    baseURL: '/api/v1', // API endpoint prefix
    headers: {
        'Content-Type': 'application/json',
    },
});

export default client;
