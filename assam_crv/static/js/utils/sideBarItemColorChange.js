function colorChange(id, adminEleId) {
    if (id) {
        const currentPath = window.location.pathname;
        const ele = currentPath.includes('administrator')
            ? document.getElementById(adminEleId)
            : document.getElementById(id);

        if (currentPath && currentPath.includes(String(id))) {
            // Background + text
            ele.style.backgroundColor = "#245FAE";

            // Change the sidebar text
            const textEl = ele.querySelector(".sideBarText");
            if (textEl) {
                textEl.style.color = "#FFFFFF";
            }

            // Change old <i> icons
            ele.querySelectorAll("i").forEach(icon => {
                icon.style.color = "#FFFFFF";
            });

            // Change new <svg> icons
            ele.querySelectorAll("svg").forEach(svg => {
                svg.querySelectorAll("path, rect, circle").forEach(path => {
                    path.setAttribute("fill", "#FFFFFF");
                    path.setAttribute("stroke", "#FFFFFF");
                    path.style.fill = "#FFFFFF"; 
                });
            });
        }

        if (document.getElementById('sideBarToggler')) {
            reFreshSelect();
        }
    }
}



function reFreshSelect(){
    const sidebarToggleBtn = document.getElementById('sideBarToggler');

    sidebarToggleBtn.addEventListener('click', () => {
        const filterSection = document.getElementById('filter');
        
        if (!filterSection) return; // Guard clause if filter section doesn't exist

        // Force layout reflow with a slightly longer delay to match sidebar transition
       
        setTimeout(() => {
            //  filterSection.style.display = 'none';
            filterSection.style.display = 'block';

            // Safe Select2 reinitialization
            if (window.jQuery && $.fn.select2) {
                $('#filter select.select2').each(function () {
                    const $this = $(this);
                    
                    // Check if already initialized
                    if ($this.hasClass('select2-hidden-accessible')) {
                        $this.select2('destroy');
                    }

                    $this.select2({
                        width: '100%' // Force full width
                    }); // Re-init
                });
            }

        }, 300); // Increased delay to match sidebar transition
    });
}

// async function getApprovedListOfModules(params) {
//     try {
//         let api_res = await fetch(`/api/get_modules_permission/`, {
//             method: 'GET',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': getCSRFToken()
//             }
//         })
//         let json_res = await api_res.json()   
//         console.log('get_modules_permission-> ',json_res)
//         if(json_res && json_res.length) {
//             json_res.forEach(ele => {
//                 if(document.getElementById(ele.div_id))
//                 {
//                     document.getElementById(ele.div_id).style.display="flex"
//                 }
//             });
//         }
//     } catch (error) {
//         console.log(error)
//     }
// }

document.addEventListener('DOMContentLoaded', function () {

    // getApprovedListOfModules()
});