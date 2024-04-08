/* Set movie descriptions for the main page */


// Generate an initial plot on load and set a handler to the generate button
$(function() {
	$(document).ready(function() {
        setContent();
        listMovies();
        setPersonContent();
    });
  	$("#generate_button").bind("click", function() {setContent()});
  	$("#generate_person_button").bind("click", function() {setPersonContent()});
});

/**
 * Backend request for new movie content.
 * @param   {String} path   optional path to a bucket file to fetch.
 *                          if not provided, a random content is fetched.
 */
function setContent(path) {
    $.ajax({
        beforeSend: function(request) {
            request.setRequestHeader("X-Button-Callback", "true");
            // Hide content and display the loader
            $(".loader").show();
            $("#movie_title").empty();
            $("#original_movie_title").empty();
            $("#plot").empty();
            $("#cast").empty();
            $("#movie-info-table .infobox-data-row").remove();
        },
        dataType: "json",
        url: "/_get",
        // Add path as query parameter if provided
        data: path ? {"path": path} : undefined,
        success: function(data) {
            // Set description content and hide loader
            $(".loader").hide();
            $("#movie_title").html(data.metadata.title);
            $("#original_movie_title").html(
                `<a href="https://en.wikipedia.org/wiki/${data.metadata.url_title}">
                    (${data.metadata.original_movie_title})</a>`
            );
            $("#plot").html(data.plot);
            $("#cast").html(data.cast);
            updateInfobox("#movie-info-table", data);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $(".loader").empty();
            $("#movie_title").html("<h1>Something went wrong, try again</h1>");
            $("#original_movie_title").empty();
            $("#plot").empty();
            $("#cast").empty();
            $("#movie-info-table .infobox-data-row").remove();
        }
    });
    return false;
}

/**
 * Update the poster image and key, value fields in the metadata sections.
 * @param  {String} boxId   id of the table element to modify
 * @param  {Object} data    the data to write
 */
function updateInfobox(boxId, data) {
    $(".infobox-image-ref").attr("src", data.img);

    // Dynamically create a table row for each infobox item
    var tableHtml = "";
    for (const key in data.infobox) {
        tableHtml += `<tr class="infobox-data-row">
            <th class="infobox-header">${key}</th>
            <td class="infobox-data">${data.infobox[key]}</td>
        </tr>`
    }
    $(boxId + " tr:last").after(tableHtml);
}

/* Fetch current movie list from the bucket and display as a list. */
function listMovies() {
    $.ajax({
        dataType: "json",
        url: "/_get_movie_list",
        success: function(data) {
            for (const movie in data) {
                var li = $(`<li><a href="#">${movie}</a></li>`)
                li.attr("data-bucket-path", data[movie]);

                // set the click callback to show the main section and
                // update the content accordingly.
                li.on("click", function() { 
                    $('#nav-tab-list a[href="#home"]').tab('show');
                    setContent(data[movie]) }
                );

                $("#movie-list > ul").append(li);
            }
        }
    })
}

/* Fetch and display a new person to show in the people section. */ 
function setPersonContent() {
    $.ajax({
        beforeSend: function(request) {
            request.setRequestHeader("X-Button-Callback", "true");
            $("#person_title").empty();
            $("#original_person_title").empty();
            $("#person-description").empty();
            $("#person-info-table .infobox-data-row").remove();
            $(".loader").show();
        },
        dataType: "json",
        url: "/_get_person",
        success: function(data) {
            $("#person_title").html(data.metadata.title);
            $("#original_person_title").html(
                `<a href="https://en.wikipedia.org/wiki/${data.metadata.url_title}">
                    (${data.metadata.original_title})</a>`
            );

            $("#person-description").html(data.description);
            $(".loader").hide();
            updateInfobox("#person-info-table", data);

            // update metadata table image labels
            $(".infobox-image-ref")[1].alt = data.img_prompt + " | Image created with DALL·E 2"
            $(".infobox-image-ref")[1].title = data.img_prompt + " | Image created with DALL·E 2"
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $("#person_title").html("<h1>Something went wrong, try again</h1>");
            $("#original_person_title").empty();
            $("#person-description").empty();
            $("#person-info-table .infobox-data-row").remove();
            $(".loader").empty();
        }
    });
    return false;
}
