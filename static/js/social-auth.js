document.addEventListener('DOMContentLoaded', () => {
    // Social authentication buttons
    const facebookAuthBtn = document.getElementById('facebook-auth');
    const appleAuthBtn = document.getElementById('apple-auth');
    const phoneAuthBtn = document.getElementById('phone-auth');

    // Facebook authentication
    if (facebookAuthBtn) {
        facebookAuthBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/auth/facebook', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    showError('Facebook authentication failed');
                }
            } catch (error) {
                console.error('Facebook auth error:', error);
                showError('Failed to connect to Facebook');
            }
        });
    }

    // Apple authentication
    if (appleAuthBtn) {
        appleAuthBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/auth/apple', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    showError('Apple authentication failed');
                }
            } catch (error) {
                console.error('Apple auth error:', error);
                showError('Failed to connect to Apple');
            }
        });
    }

    // Phone authentication
    if (phoneAuthBtn) {
        phoneAuthBtn.addEventListener('click', async () => {
            try {
                const phoneNumber = prompt('Please enter your phone number:');
                if (!phoneNumber) return;

                const response = await fetch('/auth/phone', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ phoneNumber })
                });
                const data = await response.json();
                if (data.success) {
                    const verificationCode = prompt('Please enter the verification code:');
                    if (!verificationCode) return;

                    const verifyResponse = await fetch('/auth/phone/verify', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ phoneNumber, code: verificationCode })
                    });
                    const verifyData = await verifyResponse.json();
                    if (verifyData.success) {
                        window.location.href = verifyData.redirect;
                    } else {
                        showError('Invalid verification code');
                    }
                } else {
                    showError('Phone authentication failed');
                }
            } catch (error) {
                console.error('Phone auth error:', error);
                showError('Failed to authenticate with phone');
            }
        });
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.querySelector('.auth-form').appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }
}));