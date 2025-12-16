let sideBarOpened=true
function toggleSidebar() {

    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const sideBarTexts = document.getElementsByClassName('sideBarText');
    const footer = document.querySelector('footer');
    // console.log("Width-> ", sidebar.style.width)

    if (sidebar.style.width === '3.5rem' || !sideBarOpened) {
        // Expand sidebar
        mainContent.style.width = 'calc(100% - 300px)';
        sidebar.style.width = '300px';
        mainContent.style.marginLeft = '300px';
        
      

        // Make sidebar touch the bottom
        // sidebar.style.height = 'calc(100% - 6.8rem)';

        setTimeout(() => {
            Array.from(sideBarTexts).forEach(el => {
                el.style.display = "block";
            });
        }, 300);
         footer.style.width = 'calc(100% - 300px)';
            footer.style.marginLeft = '300px';
          // Small delay for footer to make transition smoother
        // setTimeout(() => {
        //     footer.style.width = 'calc(100% - 319px)';
        //     footer.style.marginLeft = '319px';
        // }, 300);
    } else {
        // Collapse sidebar
        Array.from(sideBarTexts).forEach(el => {
            el.style.display = "none";
        });

        sidebar.style.width = '3.5rem';
        mainContent.style.marginLeft = '3.5rem';
          // Small delay for footer to make transition smoother
        // setTimeout(() => {
        //     footer.style.width = 'calc(100% - 3.5rem)';
        //     footer.style.marginLeft = '3.5rem';
        // }, 300);

             footer.style.width = 'calc(100% - 3.5rem)';
            footer.style.marginLeft = '3.5rem';

        mainContent.style.width = 'calc(100% - 3.5rem)';
        
      
    }
    sideBarOpened=!sideBarOpened;
}



// Custom Dropdown Functionality for the mobile view

function initializeDropdown() {
    const dropdownButton = document.getElementById('dropdownMenuButton');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (!dropdownButton || !dropdownMenu) {
        console.warn('Dropdown elements not found');
        return;
    }
    
    // Toggle dropdown on button click
    dropdownButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Toggle the dropdown visibility
        const isVisible = dropdownMenu.style.display === 'block';
        
        if (isVisible) {
            hideDropdown();
        } else {
            showDropdown();
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
            hideDropdown();
        }
    });
    
    // Close dropdown when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideDropdown();
        }
    });
    
    // Handle dropdown item clicks
    const dropdownItems = dropdownMenu.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Allow the link to work normally
            // Hide dropdown after a short delay to allow navigation
            setTimeout(() => {
                hideDropdown();
            }, 100);
        });
    });
}

function showDropdown() {
    const dropdownMenu = document.querySelector('.dropdown-menu');
    const dropdownButton = document.getElementById('dropdownMenuButton');
    
    if (dropdownMenu && dropdownButton) {
        dropdownMenu.style.display = 'block';
        dropdownButton.setAttribute('aria-expanded', 'true');
        
        // Add active class for styling
        dropdownButton.classList.add('dropdown-active');
    }
}

function hideDropdown() {
    const dropdownMenu = document.querySelector('.dropdown-menu');
    const dropdownButton = document.getElementById('dropdownMenuButton');
    
    if (dropdownMenu && dropdownButton) {
        dropdownMenu.style.display = 'none';
        dropdownButton.setAttribute('aria-expanded', 'false');
        
        // Remove active class
        dropdownButton.classList.remove('dropdown-active');
    }
}

// Function to initialize the layout
function initializeLayout() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const footer = document.querySelector('footer');
    
    // Check if sidebar is expanded or collapsed
    if (sidebar.style.width === '300px' || sideBarOpened) {
        // Expanded sidebar
        mainContent.style.width = 'calc(100% - 300px)';
        mainContent.style.marginLeft = '300px';
        footer.style.width = 'calc(100% - 300px)';
        footer.style.marginLeft = '300px';
    } else {
        // Collapsed sidebar
        mainContent.style.width = 'calc(100% - 3.5rem)';
        mainContent.style.marginLeft = '3.5rem';
        footer.style.width = 'calc(100% - 3.5rem)';
        footer.style.marginLeft = '3.5rem';
    }
    
    // Ensure sidebar touches the bottom
    // sidebar.style.height = 'calc(100% - 6.8rem)';
}

// Initialize dropdown when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDropdown();
    initializeLayout();
    document.getElementById('sideBarToggler').addEventListener('click',()=>{
        toggleSidebar()
    });
    
    // Add window resize event listener
    window.addEventListener('resize', function() {
        initializeLayout();
    });
});

// Alternative: If you're loading this script after the DOM is ready
// You can also call initializeDropdown() directly
// initializeDropdown();


function toggleSideBarInMob(){
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const footer = document.querySelector('footer');
    
    if (sidebar.classList.contains('d-none')) {
        sidebar.classList.remove('d-none');
        sidebar.classList.add('d-block');
        
        // Ensure sidebar touches the bottom in mobile view
        sidebar.style.height = 'calc(100% - 10.4rem)';
        
        // On mobile, when sidebar is shown, adjust content and footer
        if (window.innerWidth <= 500) {
            mainContent.style.marginLeft = '0';
            footer.style.width = '100%';
            footer.style.marginLeft = '0';
        }
    } else {
        sidebar.classList.remove('d-block');
        sidebar.classList.add('d-none');
        
        // Reset content and footer on mobile when sidebar is hidden
        if (window.innerWidth <= 500) {
            mainContent.style.marginLeft = '0';
            footer.style.width = '100%';
            footer.style.marginLeft = '0';
        }
    }
}