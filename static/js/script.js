document.addEventListener('DOMContentLoaded', function () {
    const characterForm = document.getElementById('characterForm');

    if (characterForm) {
        characterForm.addEventListener('submit', function (event) {
            // Prevent the default form submission
            event.preventDefault();

            const region = document.getElementById('region').value;
            const realm = document.getElementById('realm').value;
            const character = document.getElementById('character').value;

            // Validate inputs
            if (!realm || !character) {
                alert('Please fill in all required fields');
                return false;
            }

            // Clean up the inputs
            const cleanRealm = realm.trim().toLowerCase().replace(/\s+/g, '-');
            const cleanCharacter = character.trim();

            // Redirect to the character page
            window.location.href = `/character/${region}/${cleanRealm}/${cleanCharacter}`;
        });
    }

    // Add click handler for the button as a backup in case form submission doesn't work
    const lookupButton = document.querySelector('#characterForm button[type="submit"]');
    if (lookupButton) {
        lookupButton.addEventListener('click', function () {
            // Trigger form submission
            if (characterForm) {
                characterForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    console.log('Character form handlers initialized');
});