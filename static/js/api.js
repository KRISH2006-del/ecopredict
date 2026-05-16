/**
 * API Module - Handles all server communication
 * Uses ES6 module pattern with async/await
 */

export class ApiService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * Make a prediction request
     */
    async predict(formData) {
        try {
            const response = await fetch(`${this.baseUrl}/predict`, {
                method: 'POST',
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error('Prediction API Error:', error);
            throw error;
        }
    }

    /**
     * Fetch statistics for charts
     */
    async getStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/stats`);
            return await response.json();
        } catch (error) {
            console.error('Stats API Error:', error);
            throw error;
        }
    }
}

export default ApiService;
