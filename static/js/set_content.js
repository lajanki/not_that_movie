/* Set movie descriptions for the main page */


// Generate an initial plot on load and set a handler to the generate button
$(function() {
	$(document).ready(function() { setContent(); listMovies(); });
  	$("#generate_button").bind("click", function() {setContent()});
});

/* Backend request for new random content. */ 
function setContent(path) {
    $.ajax({
        beforeSend: function(request) {
            request.setRequestHeader("X-Button-Callback", "true");
            // Hide content and display the loader
            $("#movie_title").empty();
            $("#original_title").empty();   
            $("#plot").empty();
            $("#cast").empty();
            $("#metadata").empty();
            $(".infobox-data-row").remove();
            $("#loader").show();
        },
        dataType: "json",
        url: "/_get",
        // Add path as query parameter if provided
        data: path ? {"path": path} : undefined,
        success: function(data) {
            // Set description content and hide loader
            $("#loader").hide();
            $("#movie_title").html(data.metadata.title);
            $("#original_title").html("(" + data.metadata.original_title + ")");
            $("#plot").html(data.plot);
            $("#cast").html(data.cast);
            updateInfobox(data);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#movie_title").html("<h1>Something went wrong, try again</h1>");
            $("#cast").empty();
            $("#metadata").empty();
            $("#loader").empty();
        }
    });
    return false;
}

/* Update the poster image and key, value fields in the infobox. */
function updateInfobox(data) {
    $("#infobox-image-ref").attr("src", data.img);

    // Dynamically create a table row for each infobox item
    var tableHtml = "";
    for (const key in data.infobox) {
        tableHtml += `<tr class="infobox-data-row">
            <th class="infobox-header">${key}</th>
            <td class="infobox-data">${data.infobox[key]}</td>
        </tr>`
    }
    $("#infobox tr:last").after(tableHtml);
}

function setContentTo(path) {
    $('#nav-tab-list a[href="#home"]').tab('show');
    setContent(path);
}

/* Fetch current movies from the bucket and list as index. */
function listMovies() {
    $.ajax({
        dataType: "json",
        url: "/_get_movie_list",
        success: function(data) {
            for (const movie in data) {
                var li = $(`<li><a href="#">${movie}</a></li>`)
                li.attr("data-bucket-path", data[movie]);

                li.on("click", function() { setContentTo(data[movie]) });
                $("#movie-list > ul").append(li);
            }
        }
    })
}
