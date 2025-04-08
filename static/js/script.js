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

document.addEventListener('DOMContentLoaded', () => {
    // List of all WoW realms
    const realms = [
        // US Pacific - PvE
        "Aerie Peak", "Akama", "Andorhal", "Antonidas", "Arathor", "Baelgun", "Blackrock", 
        "Borean Tundra", "Bonechewer", "Cairne", "Cenarius", "Coilfang", "Dalvengyr", 
        "Dark Iron", "Daggerspine", "Deathwing", "Demon Soul", "Doomhammer", "Draenor", 
        "Dragonblight", "Dragonmaw", "Drakthul", "Draka", "Drenden", "Echo Isles", 
        "Executus", "Fenris", "Frostwolf", "Gnomeregan", "Hyjal", "Kalecgos", 
        "KilJaeden", "Kilrogg", "Lightbringer", "MokNathal", "Moonrunner", "Mugthol", 
        "Perenolde", "Proudmoore", "Scilla", "Shadowsong", "Shandris", "Shattered Halls", 
        "Shattered Hand", "Silvermoon", "Skywall", "Suramar", "Tichondrius", "Uldum", 
        "Ursin", "Vashj", "Windrunner", "Winterhoof", "Zuluhed",
        
        // US Pacific - RP
        "Cenarion Circle", "Farstriders", "Feathermoon", "Scarlet Crusade", 
        "Silver Hand", "Sisters of Elune", "Thorium Brotherhood", "Wyrmrest Accord",
        
        // US Mountain - PvE
        "Azjol-Nerub", "Bloodscalp", "Boulderfist", "Darkspear", "Dunemaul", 
        "Hydraxis", "KelThuzad", "Khaz Modan", "Maiev", "Stonemaul", "Terenas",
        
        // US Mountain - RP
        "Blackwater Raiders", "Shadow Council",
        
        // US Central - PvE
        "Aegwynn", "Agamaggan", "Aggramar", "Akama", "Alexstrasza", "Alleria", 
        "Anubarak", "Anvilmar", "Archimonde", "Auchindoun", "Azgalor", "Azshara", 
        "Azuremist", "Blackhand", "Blackwing Lair", "Blades Edge", "Bladefist", 
        "Bonechewer", "Burning Legion", "Chogall", "Chromaggus", "Crushridge", 
        "Daggerspine", "Dawnbringer", "Dentarg", "Destromath", "Dethecus", "Detheroc", 
        "Eitrigg", "Eredar", "Fizzcrank", "Frostmane", "Galakrond", "Garithos", "Garona", 
        "Ghostlands", "Gorefiend", "Greymane", "Gurubashi", "Hakkar", "Haomarush", 
        "Hellscream", "Icecrown", "Illidan", "Jaedenar", "Kaelthas", "Khadgar", 
        "Korgath", "Kul Tiras", "Laughing Skull", "Lethon", "Madoran", "MalGanis", 
        "Malygos", "Misha", "Muradin", "Nathrezim", "Nazgrel", "Nerzhul", "Nesingwary", 
        "Nordrassil", "QuelDorei", "Ravencrest", "Rexxar", "Runetotem", "Sargeras", 
        "SenJin", "Shadowmoon", "Shuhalo", "Smolderthorn", "Spinebreaker", "Staghelm", 
        "Stormreaver", "Tanaris", "Terokkar", "The Underbog", "Thunderhorn", "Thunderlord", 
        "Tortheldrin", "Uldaman", "Undermine", "Uther", "Veknilash", "Whisperwind", 
        "Wildhammer", "Zangarmarsh",
        
        // US Central - RP
        "Emerald Dream", "Kirin Tor", "Lightninghoof", "Maelstrom", "Moon Guard", 
        "Ravenholdt", "Sentinels", "Steamwheedle Cartel", "The Venture Co", "Twisting Nether",
        
        // US Eastern - PvE
        "Altar of Storms", "Alterac Mountains", "Anetheron", "Area 52", "Arthas", 
        "Arygos", "Balnazzar", "Black Dragonflight", "Bleeding Hollow", "Blood Furnace", 
        "Bloodhoof", "Burning Blade", "Dalaran", "DrakTharon", "Durotan", "Duskwood", 
        "EldreThalas", "Elune", "Eonar", "Exodar", "Firetree", "Garrosh", "Gilneas", 
        "Gorgonnash", "Grizzly Hills", "Guldan", "Kargath", "Korialstrasz", 
        "Lightnings Blade", "Llane", "Lothar", "Magtheridon", "Malfurion", "Malorne", 
        "Mannoroth", "Medivh", "Nazjatar", "Norgannon", "Onyxia", "Rivendare", 
        "Skullcrusher", "Spirestone", "Stormrage", "Stormscale", "The Forgotten Coast", 
        "Thrall", "Trollbane", "Turalyon", "Velen", "Warsong", "Ysera", "Ysondre", "Zuljin",
        
        // US Eastern - RP
        "Argent Dawn", "Earthen Ring", "The Scryers",
        
        // Oceanic - PvE
        "AmanThul", "Barthilas", "Caelestrasz", "DathRemar", "Dreadmaul", 
        "Frostmourne", "Gundrak", "JubeiThos", "Khazgoroth", "Nagrand", 
        "Saurfang", "Thaurissan",
        
        // Latin America - PvE
        "Drakkari", "QuelThalas", "Ragnaros",
        
        // Brazil - PvE
        "Azralon", "Gallywix", "Goldrinn", "Nemesis", "Tol Barad"
    ];

    const realmInput = document.getElementById('realm');
    const suggestionContainer = document.createElement('div');
    suggestionContainer.className = 'suggestion-container';
    suggestionContainer.style.display = 'none';
    suggestionContainer.style.position = 'absolute';
    suggestionContainer.style.width = `${realmInput.offsetWidth}px`;
    suggestionContainer.style.maxHeight = '200px';
    suggestionContainer.style.overflowY = 'auto';
    suggestionContainer.style.border = '1px solid #ced4da';
    suggestionContainer.style.borderRadius = '0 0 4px 4px';
    suggestionContainer.style.backgroundColor = '#fff';
    suggestionContainer.style.zIndex = '1000';
    suggestionContainer.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    
    // Insert the suggestion container after the realm input
    realmInput.parentNode.style.position = 'relative';
    realmInput.parentNode.appendChild(suggestionContainer);

    // Debounce function
    function debounce(func, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Function to filter realms based on input
    function filterRealms(inputValue) {
        if (!inputValue) {
            return [];
        }
        
        inputValue = inputValue.toLowerCase();
        return realms.filter(realm => 
            realm.toLowerCase().includes(inputValue)
        ).slice(0, 10); // Limit to 10 suggestions for better UX
    }

    // Function to display suggestions
    function displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            suggestionContainer.style.display = 'none';
            return;
        }

        suggestionContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.textContent = suggestion;
            item.className = 'suggestion-item';
            item.style.padding = '8px 12px';
            item.style.cursor = 'pointer';
            
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f0f0f0';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'transparent';
            });
            
            item.addEventListener('click', () => {
                realmInput.value = suggestion;
                suggestionContainer.style.display = 'none';
            });
            
            suggestionContainer.appendChild(item);
        });
        
        suggestionContainer.style.display = 'block';
    }

    // Handle input changes with debounce
    const handleInput = debounce((e) => {
        const inputValue = e.target.value;
        const filteredRealms = filterRealms(inputValue);
        displaySuggestions(filteredRealms);
    }, 300); // 300ms debounce delay

    // Add event listeners
    realmInput.addEventListener('input', handleInput);
    
    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target !== realmInput && e.target !== suggestionContainer) {
            suggestionContainer.style.display = 'none';
        }
    });

    // Handle keyboard navigation through suggestions
    realmInput.addEventListener('keydown', (e) => {
        if (suggestionContainer.style.display === 'none') return;
        
        const items = suggestionContainer.querySelectorAll('.suggestion-item');
        let activeIndex = Array.from(items).findIndex(item => 
            item.style.backgroundColor === '#f0f0f0'
        );
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (activeIndex < items.length - 1) {
                    if (activeIndex >= 0) items[activeIndex].style.backgroundColor = 'transparent';
                    activeIndex++;
                    items[activeIndex].style.backgroundColor = '#f0f0f0';
                    items[activeIndex].scrollIntoView({ block: 'nearest' });
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (activeIndex > 0) {
                    items[activeIndex].style.backgroundColor = 'transparent';
                    activeIndex--;
                    items[activeIndex].style.backgroundColor = '#f0f0f0';
                    items[activeIndex].scrollIntoView({ block: 'nearest' });
                }
                break;
                
            case 'Enter':
                if (activeIndex >= 0) {
                    e.preventDefault();
                    realmInput.value = items[activeIndex].textContent;
                    suggestionContainer.style.display = 'none';
                }
                break;
                
            case 'Escape':
                suggestionContainer.style.display = 'none';
                break;
        }
    });
});