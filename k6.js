// Import necessary libraries
import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
    stages: [
        // Ramp-up from 1 to 50 users over 1 minute
        { duration: '1m', target: 500 },

        // Stay at peak (100 users) for 3 minutes
        { duration: '3m', target: 500 },

        // Ramp-down to 0 users over 1 minute
        { duration: '1m', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(99)<1500'],  // 99% of requests must complete below 1500ms
    },
};

export default function () {
    // Define the HTTP request
    let response = http.get('https://fitness.dev.one-click.dev/');

    // Optionally, check response status and log errors
    check(response, {
        'status is 200': (r) => r.status === 200,
    });

    // Think time
    sleep(1);
}
