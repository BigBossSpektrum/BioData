/**
 * Sistema de manejo de timeout de sesión
 * Administra el cierre automático de sesión cada 30 minutos
 */

class SessionManager {
    constructor() {
        this.timeoutDuration = 30 * 60 * 1000; // 30 minutos en milisegundos
        this.warningTime = 5 * 60 * 1000; // Advertencia 5 minutos antes
        this.checkInterval = 60 * 1000; // Verificar cada minuto
        
        this.sessionTimeout = null;
        this.warningTimeout = null;
        this.checkTimer = null;
        
        this.isWarningShown = false;
        this.lastActivity = Date.now();
        
        this.init();
    }
    
    init() {
        // Obtener información de la sesión del servidor
        this.getSessionInfo();
        
        // Configurar eventos de actividad
        this.setupActivityListeners();
        
        // Iniciar verificación periódica
        this.startPeriodicCheck();
        
        console.log('SessionManager iniciado - timeout de 30 minutos');
    }
    
    getSessionInfo() {
        // Intentar obtener información de la sesión desde el template
        const sessionData = document.querySelector('meta[name="session-data"]');
        if (sessionData) {
            try {
                const data = JSON.parse(sessionData.content);
                this.lastActivity = data.lastActivity * 1000; // Convertir a milisegundos
            } catch (e) {
                console.warn('No se pudo parsear la información de sesión');
            }
        }
    }
    
    setupActivityListeners() {
        // Eventos que consideramos como actividad del usuario
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.resetTimer();
            }, true);
        });
        
        // También monitorear peticiones AJAX
        this.interceptAjaxRequests();
    }
    
    interceptAjaxRequests() {
        // Interceptar fetch
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.resetTimer();
            return originalFetch.apply(this, args)
                .then(response => {
                    // Verificar si la respuesta indica sesión expirada
                    if (response.status === 401) {
                        response.clone().json().then(data => {
                            if (data.session_expired) {
                                this.handleSessionExpired(data.message);
                            }
                        }).catch(() => {});
                    }
                    return response;
                });
        };
        
        // Interceptar XMLHttpRequest
        const originalXHR = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(...args) {
            this.addEventListener('loadstart', () => {
                window.sessionManager?.resetTimer();
            });
            
            this.addEventListener('load', () => {
                if (this.status === 401) {
                    try {
                        const data = JSON.parse(this.responseText);
                        if (data.session_expired) {
                            window.sessionManager?.handleSessionExpired(data.message);
                        }
                    } catch (e) {}
                }
            });
            
            return originalXHR.apply(this, args);
        };
    }
    
    resetTimer() {
        this.lastActivity = Date.now();
        
        // Limpiar timers existentes
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
        }
        if (this.warningTimeout) {
            clearTimeout(this.warningTimeout);
        }
        
        // Ocultar advertencia si está visible
        this.hideWarning();
        
        // Configurar nuevos timers
        this.warningTimeout = setTimeout(() => {
            this.showWarning();
        }, this.timeoutDuration - this.warningTime);
        
        this.sessionTimeout = setTimeout(() => {
            this.handleSessionExpired();
        }, this.timeoutDuration);
    }
    
    startPeriodicCheck() {
        this.checkTimer = setInterval(() => {
            const now = Date.now();
            const timeSinceActivity = now - this.lastActivity;
            
            // Si han pasado más de 30 minutos, cerrar sesión
            if (timeSinceActivity >= this.timeoutDuration) {
                this.handleSessionExpired();
                return;
            }
            
            // Si faltan 5 minutos o menos, mostrar advertencia
            if (timeSinceActivity >= (this.timeoutDuration - this.warningTime) && !this.isWarningShown) {
                this.showWarning();
            }
        }, this.checkInterval);
    }
    
    showWarning() {
        if (this.isWarningShown) return;
        
        this.isWarningShown = true;
        
        // Crear modal de advertencia
        const modal = this.createWarningModal();
        document.body.appendChild(modal);
        
        // Mostrar modal usando Bootstrap
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        console.log('Advertencia de sesión mostrada');
    }
    
    createWarningModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'sessionWarningModal';
        modal.setAttribute('data-bs-backdrop', 'static');
        modal.setAttribute('data-bs-keyboard', 'false');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-warning">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="bi bi-clock-history me-2"></i>
                            Advertencia de Sesión
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="mb-3">
                            <i class="bi bi-exclamation-triangle-fill text-warning" style="font-size: 3rem;"></i>
                        </div>
                        <h6>Tu sesión expirará pronto</h6>
                        <p class="mb-3">Tu sesión se cerrará automáticamente en <span id="countdown">5:00</span> minutos por inactividad.</p>
                        <p class="text-muted small">Haz clic en "Mantener Sesión" para continuar trabajando.</p>
                    </div>
                    <div class="modal-footer justify-content-center">
                        <button type="button" class="btn btn-warning" onclick="window.sessionManager.extendSession()">
                            <i class="bi bi-arrow-clockwise me-1"></i>
                            Mantener Sesión
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="window.sessionManager.logout()">
                            <i class="bi bi-box-arrow-right me-1"></i>
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Iniciar countdown
        this.startCountdown();
        
        return modal;
    }
    
    startCountdown() {
        let timeLeft = 5 * 60; // 5 minutos en segundos
        
        const countdownInterval = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            const countdownElement = document.getElementById('countdown');
            if (countdownElement) {
                countdownElement.textContent = display;
                
                // Cambiar color cuando queda poco tiempo
                if (timeLeft <= 60) {
                    countdownElement.className = 'text-danger fw-bold';
                }
            }
            
            timeLeft--;
            
            if (timeLeft < 0) {
                clearInterval(countdownInterval);
                this.handleSessionExpired();
            }
        }, 1000);
    }
    
    extendSession() {
        this.hideWarning();
        this.resetTimer();
        
        // Notificar al servidor sobre la actividad
        fetch('/accounts/extend-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({})
        }).catch(error => {
            console.warn('Error al extender sesión:', error);
        });
        
        console.log('Sesión extendida');
    }
    
    hideWarning() {
        this.isWarningShown = false;
        const modal = document.getElementById('sessionWarningModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
            modal.remove();
        }
    }
    
    handleSessionExpired(message = null) {
        console.log('Sesión expirada');
        
        // Limpiar todos los timers
        if (this.sessionTimeout) clearTimeout(this.sessionTimeout);
        if (this.warningTimeout) clearTimeout(this.warningTimeout);
        if (this.checkTimer) clearInterval(this.checkTimer);
        
        // Mostrar mensaje y redirigir
        const defaultMessage = 'Tu sesión ha expirado por inactividad. Serás redirigido al inicio de sesión.';
        alert(message || defaultMessage);
        
        // Redirigir al login
        window.location.href = '/accounts/login/';
    }
    
    logout() {
        // Cerrar sesión manualmente
        window.location.href = '/accounts/logout/';
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si el usuario está autenticado
    const userElement = document.querySelector('meta[name="user-authenticated"]');
    if (userElement && userElement.content === 'true') {
        window.sessionManager = new SessionManager();
    }
});
