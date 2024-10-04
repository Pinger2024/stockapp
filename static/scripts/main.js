// main.js

$(document).ready(function () {
    // Smooth scroll to table after filtering
    $('form').on('submit', function (e) {
        e.preventDefault(); // Prevent the form from refreshing the page
        // Perform the form submission (could be an AJAX call or letting the form submit itself)
        
        // Simulate form submission for now
        console.log("Form submitted");

        // Scroll to the stocks table smoothly
        $('html, body').animate({
            scrollTop: $('table').offset().top - 20
        }, 800);
    });

    // Highlight clicked table row
    $('.table tbody tr').on('click', function () {
        $(this).toggleClass('highlight-row');
    });
});
