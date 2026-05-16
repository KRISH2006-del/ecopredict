/**
 * UI Module - Handles UI interactions and animations
 * Uses ES6 module pattern
 */

export class UIManager {
    constructor() {
        this.animationDuration = 300;
    }

    /**
     * Show loading state on button
     */
    setButtonLoading(button, loading = true) {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<span class="spinner"></span> Processing...';
            button.disabled = true;
        } else {
            button.innerHTML = button.dataset.originalText || 'Submit';
            button.disabled = false;
        }
    }

    /**
     * Show result with animation
     */
    showResult(element, content, isSuccess = true) {
        element.innerHTML = content;
        element.className = isSuccess ? 'success visible' : 'error visible';
    }

    /**
     * Update stat cards with animation
     */
    updateStatCard(cardId, value, animate = true) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const valueElement = card.querySelector('.stat-value');
        if (!valueElement) return;

        if (animate) {
            this.animateNumber(valueElement, 0, value, 1000);
        } else {
            valueElement.textContent = this.formatNumber(value);
        }
    }

    /**
     * Animate number counting effect
     */
    animateNumber(element, start, end, duration) {
        const startTime = performance.now();
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.floor(start + (end - start) * this.easeOutQuart(progress));
            element.textContent = this.formatNumber(current);

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        requestAnimationFrame(update);
    }

    /**
     * Easing function for smooth animation
     */
    easeOutQuart(x) {
        return 1 - Math.pow(1 - x, 4);
    }

    /**
     * Format large numbers with commas
     */
    formatNumber(num) {
        return num.toLocaleString('en-US');
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

export default UIManager;
