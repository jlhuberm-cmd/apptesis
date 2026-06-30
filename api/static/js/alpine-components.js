// ============================================================
//  alpine-components.js — Componentes Alpine.js reutilizables
//  Se registran en el evento alpine:init (antes de inicializar Alpine).
// ============================================================

document.addEventListener('alpine:init', () => {
  // Indicador de fortaleza de contraseña.
  Alpine.data('passwordStrength', () => ({
    pw: '',
    confirm: '',
    show: false,
    get checks() {
      return {
        len: this.pw.length >= 8,
        upper: /[A-Z]/.test(this.pw),
        lower: /[a-z]/.test(this.pw),
        num: /[0-9]/.test(this.pw),
        spec: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(this.pw),
      };
    },
    get score() {
      return Object.values(this.checks).filter(Boolean).length;
    },
    get match() {
      return this.confirm.length > 0 && this.pw === this.confirm;
    },
  }));

  // Inputs de código OTP de N dígitos.
  Alpine.data('otpInput', (length = 6) => ({
    digits: Array(length).fill(''),
    get code() {
      return this.digits.join('');
    },
    onInput(i, e) {
      const v = (e.target.value || '').replace(/[^0-9]/g, '');
      this.digits[i] = v.slice(-1);
      e.target.value = this.digits[i];
      if (this.digits[i] && i < length - 1) this.$refs['d' + (i + 1)].focus();
    },
    onKey(i, e) {
      if (e.key === 'Backspace' && !this.digits[i] && i > 0) {
        this.$refs['d' + (i - 1)].focus();
      }
    },
  }));

  // Panel de filtros: limpia los selects y vuelve a solicitar los datos.
  Alpine.data('filterPanel', () => ({
    clear() {
      const form = this.$root.closest('form') || this.$root;
      form.querySelectorAll('select').forEach((s) => (s.value = ''));
      if (window.htmx) htmx.trigger(form, 'submit');
    },
  }));
});
