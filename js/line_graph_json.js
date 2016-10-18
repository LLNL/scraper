
<!-- hide script from old browsers
var main_file_path = "../github_stats_output/total.csv"
var views_file_path = "../github_stats_output/views.csv"
var clones_file_path = "../github_stats_output/clones.csv"
create_line_graph("repos", new Date(2016,7,4,0,0,0), "repositories", "Repositories", main_file_path);
create_line_graph("members", new Date(2016,7,4,0,0,0), "members", "Members", main_file_path);
create_line_graph("teams", new Date(2016,7,4,0,0,0), "teams", "Teams", main_file_path);
create_line_graph("unique_contributors", new Date(2016,7,4,0,0,0), "unique contributors", "Unique Contributors", main_file_path);
create_line_graph("total_contributors", new Date(2016,7,4,0,0,0), "total contributors", "Total Contributors", main_file_path);
create_line_graph("forks", new Date(2016,7,4,0,0,0), "forks", "Forks", main_file_path);
create_line_graph("stargazers", new Date(2008,9,23,0,0,0), "stargazers", "Stargazers", main_file_path);
create_line_graph("pull_requests", new Date(2016,7,4,0,0,0), "total pull requests", "Total Pull Requests", main_file_path);
create_line_graph("pull_requests_open", new Date(2016,7,10,0,0,0), "open pull requests", "Open Pull Requests", main_file_path);
create_line_graph("pull_requests_closed", new Date(2016,7,10,0,0,0), "closed pull requests", "Closed Pull Requests", main_file_path);
create_line_graph("issues", new Date(2016,7,20,0,0,0), "total issues", "Total Issues", main_file_path);
create_line_graph("open_issues", new Date(2016,7,4,0,0,0), "open issues", "Open Issues", main_file_path);
create_line_graph("closed_issues", new Date(2016,7,20,0,0,0), "closed issues", "Closed Issues", main_file_path);
create_line_graph("commits", new Date(2015,7,21,0,0,0), "commits", "Commits", main_file_path);
create_line_graph("views", new Date(2016,7,4,0,0,0), "total views", "Total Views per Day", views_file_path);
create_line_graph("unique_views", new Date(2016,7,4,0,0,0), "unique views", "Unique Views per Day", views_file_path);
create_line_graph("clones", new Date(2016,7,4,0,0,0), "total clones", "Total Clones per Day", clones_file_path);
create_line_graph("unique_clones", new Date(2016,7,4,0,0,0), "unique clones", "Unique Clones per Day", clones_file_path);

function create_line_graph(name, startDate, tooltip_unit, title, file_path){
    // Set the dimensions of the canvas / graph
    var	margin = {top: 30, right: 20, bottom: 50, left: 50},
    	width = 450 - margin.left - margin.right,
    	height = 240 - margin.top - margin.bottom;

    // Parse the date / time
    var	parseDate = d3.time.format("%Y-%m-%d").parse;

    // Set the ranges
    var	x = d3.time.scale().range([0, width]);

    var	y = d3.scale.linear().range([height, 0]);

    // Define the axes
    var	xAxis = d3.svg.axis().scale(x)
    	.orient("bottom").ticks(5);

    var	yAxis = d3.svg.axis().scale(y)
    	.orient("left").ticks(5);

    //Percents used for setting axis numbers based on data
    var minPercent = 0.97;

    var maxPercent = 1.03;

    // Adds the svg canvas
    var	chart = d3.select("body")
    	.append("svg")
    		.attr("width", width + margin.left + margin.right)
    		.attr("height", height + margin.top + margin.bottom)
            //Hover over for line highlight, and line
            .on("mousemove", function(d) {
                d3.select("#line_" + name)
                    .style("stroke-width", "4");
                d3.select("#display_dots_" + name).selectAll("circle")
                    .attr("r", 4)
                    .style("fill", "steelblue");
            })
            //Hover out for dots at data points, and line.
            .on("mouseout", function(d) {
                d3.select("#display_dots_" + name).selectAll("circle")
                    .attr("r", 4)
                    .style("fill", "transparent");
                d3.select("#line_" + name)
                    .style("stroke-width", "2");
            })
    	.append("g")
    		.attr("transform", "translate(" + margin.left + "," + margin.top
            + ")");

    // Get the data
    d3.csv(file_path, function(error, data) {
    	data.forEach(function(d) {
    		d.date = parseDate(d.date);
            d[name] = +d[name];

    	});

        //Filter based on the date first gathering data
        data = data.filter(function(d) {
          return d.date > startDate;
        })

        //Define tooltip for the first chart.
        var tip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        //Define the line for the first chart.
        var	line = d3.svg.line()
            .interpolate("monotone")
        	.x(function(d) { return x(d.date); })
        	.y(function(d) { return y(d[name]); });

    	// Scale the range of the data
        max = d3.max(data, function(d) { return d[name]; })
        min = d3.min(data, function(d) { return d[name]; })
    	x.domain(d3.extent(data, function(d) { return d.date; }))
    	y.domain([minPercent * min, maxPercent * max]);

    	// Add the repo_line path.
    	chart.append("path")
    		.attr("class", "line")
    		.attr("d", line(data))
            .attr("id", "line_" + name);

            //Define the points for displaying the data points on mouse hover
            var display_dots = chart.append("g")
            .attr("id", "display_dots_" + name);

            /**
            Defime the ellipses used for seeing if the mouse is hovering over a
            data point. They are invisable and used so that the mouse can hover
            over a data point, regardless of the the y-axis point, and still
            have the data point highlighted brown over the standard blue
            highlight.
            **/
            var big_dots = chart.append("g")
            .attr("id", "big_dots_" + name);

            display_dots.selectAll("dot")
            .data(data)
            .enter()
            .append("circle")
            .attr("r", 4)
            .attr("cx", function(d) { return x(d.date); })
            .attr("cy", function(d) { return y(d[name]); })
            .style("fill", "transparent")

            big_dots.selectAll("dot")
            .data(data)
            .enter()
            .append("circle")
            .attr("r", 6)
            .attr("cx", function(d) { return x(d.date); })
            .attr("cy", function(d) { return y(d[name]); })
            .style("fill", "transparent")
            .attr("id", function(d) { return String("dot_" + name + d.id); });

            // Add the hover points
            chart.selectAll("dot")
            .data(data)
            .enter().append("ellipse")
            .attr("rx", 8)
            .attr("ry", 250)
            .attr("cx", function(d) { return x(d.date); })
            .attr("cy", function(d) { return y(d[name]); })
            .style("fill", "transparent")
            .on("mousemove", function(d) {
                //Highlight the particular data point brown
                d3.select("#" + String("dot_" + name + d.id))
                    .style("fill", "brown");
                //Turn on tooltip
                tip.transition()
                    .duration(100)
                    .style("opacity", 1.0);
                tip.html(d[name] + " " + tooltip_unit)
                    .style("left", (d3.event.pageX - 80) + "px")
                    .style("top", (d3.event.pageY - 25) + "px");
                })
                //Turn off hover over highlights of tooltip and point
            .on("mouseout", function(d) {
                d3.select("#" + String("dot_" + name + d.id))
                    .style("fill", "transparent");
                tip.transition()
                    .duration(500)
                    .style("opacity", 0);
            });

    	// Add the X Axis
    	chart.append("g")
    		.attr("class", "x axis")
    		.attr("transform", "translate(0," + height + ")")
    		.call(xAxis);

    	// Add the Y Axis
    	chart.append("g")
    		.attr("class", "y axis")
    		.call(yAxis);

        // Add the title
        chart.append("text")
            .attr("x", (width / 2))
            .attr("y", 0 - (margin.top / 2))
            .attr("text-anchor", "middle")
            .style("font-size", "16px")
            .text(title);
    });
}
// end hiding script from old browsers -->
