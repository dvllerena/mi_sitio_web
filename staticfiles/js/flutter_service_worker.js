<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('{% static "js/flutter_service_worker.js" %}');
    })
  }
</script>