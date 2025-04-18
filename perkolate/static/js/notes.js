document.addEventListener('htmx:beforeRequest', function(evt) {
    if (evt.detail.elt.id === 'noteForm') {
        const submitBtn = evt.detail.elt.querySelector('#noteSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = 'Adding...';
        }
    }
});

document.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.elt.id === 'noteForm') {
        const submitBtn = evt.detail.elt.querySelector('#noteSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Add Note';
        }
        if (evt.detail.successful) {
            evt.detail.elt.reset();
        }
    }
}); 