var language_path = "/../github_stats_output/languages.csv";
var referrer_path = "/../github_stats_output/referrers.csv";

create_bar_graph("language", "size_log", "size", "#language_size_check",
                 "Language - Size", language_path, mousemove_language_size);
create_bar_graph("language", "count", "count", "#language_count_check",
                 "Language - Repo Count", language_path,
                 mousemove_language_count);
create_bar_graph("referrer", "count_log", "count", "#refferers_size_check",
                 "Total Referrals - Previous Two Weeks", referrer_path,
                 mousemove_referrer_count);
create_bar_graph("referrer", "uniques_log", "uniques_log", "#referrers_uniques_check",
                 "Unique Referrals - Previous Two Weeks", referrer_path,
                 mousemove_referrer_unique);

function create_bar_graph(x_name, y_name, sort_name, checkbox, title, file_path,
    mousemove_callback){

    var checkbox = document.createElement('input');
    checkbox.type = "checkbox";
    checkbox.name = "name";
    checkbox.value = "value";
    checkbox.id = "id";

    var label = document.createElement('label')
    label.htmlFor = "id";
    label.appendChild(document.createTextNode('Sort ' + title));

    document.body.appendChild(checkbox);
    document.body.appendChild(label);

    var margin = {top: 20, right: 20, bottom: 125, left: 40},
        width = 1350 - margin.left - margin.right,
        height = 700 - margin.top - margin.bottom;

    var	parseDate = d3.time.format("%Y-%m-%d").parse;

    var x = d3.scale.ordinal().rangeRoundBands([0, width], .1);
    var y = d3.scale.linear().range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(10);

    var chart = d3.select("body")
       .append("div")
       .classed("svg-container", true) //container class to make it responsive
       .append("svg")
       //responsive SVG needs these 2 attributes and no width and height attr
       .attr("preserveAspectRatio", "xMinYMin meet")
       .attr("viewBox", "-50 -50 1400 800")
       //class to make it responsive
       .classed("svg-content-responsive", true);

        d3.csv(file_path, type, function(error, data) {
          if (error) throw error;
          data.forEach(function(d) {
              d.date = parseDate(d.date);
              d[y_name] = +d[y_name];
          });

        var cutoffDate = d3.max(data, function(d) { return d.date; });
        cutoffDate.setDate(cutoffDate.getDate() - 1);
        data = data.filter(function(d) {
          return d.date > cutoffDate;
        })

      x.domain(data.map(function(d) { if (d[y_name] != 0){ return d[x_name]}; }));
      y.domain([0, d3.max(data, function(d) { return d[y_name]; })]);

      chart.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis)
          .selectAll("text")
            .attr("transform", "translate(-7,0),rotate(-45)")
            .style("text-anchor", "end")


      chart.append("g")
          .attr("class", "y axis")
          .call(yAxis)
        .append("text")
          .attr("transform", "rotate(-90)")
          .attr("y", 6)
          .attr("dy", ".71em")
          .style("text-anchor", "end")
          .text("Natural Log - Size (bytes)");

      chart.selectAll(".bar")
          .data(data)
        .enter().append("rect")
          .attr("class", "bar")
          .attr("x", function(d) { return x(d[x_name]); })
          .attr("width", x.rangeBand())
          .attr("y", function(d) { return y(d[y_name]); })
          .attr("height", function(d) { return height - y(d[y_name]); })
          .on("mouseover", mouseover)
          .on("mousemove", mousemove)
          .on("mouseout", mouseout);

          var tip = d3.select("body").append("div")
              .attr("class", "tooltip")
              .style("opacity", 0);

          function mouseover() {
            tip.transition().duration(100).style("opacity", 1.0);
          }

          function mousemove(d){
              mousemove_callback(d, tip)
          }

          function mouseout() {
            tip.transition().duration(500).style("opacity", 0.0);
          }

      titleDate = d3.max(data, function(d) { return d.date; })

      // Add the title
      chart.append("text")
          .data(data)
          .attr("x", (width / 2))
          .attr("y", 0 - (margin.top / 2))
          .attr("text-anchor", "middle")
          .style("font-size", "16px")
          .text( title + " (" + titleDate + ")");

      d3.select(checkbox).on("change", change);

      var sortTimeout = setTimeout(function() {
         d3.select(checkbox).property("unchecked", true).each(change);
       }, 2000);

       function change() {
       clearTimeout(sortTimeout);

       // Copy-on-write since tweens are evaluated after a delay.
       var x0 = x.domain(data.sort(this.checked
           ? function(a, b) { return b[sort_name] - a[sort_name]; }
           : function(a, b) { return d3.ascending(a[x_name].toLowerCase(), b[x_name].toLowerCase()); })
           .map(function(d) { if(d[y_name] != 0) {return d[x_name]}; }))
           .copy();

       chart.selectAll(".bar")
           .sort(function(a, b) { return x0(a[x_name].toLowerCase()) - x0(b[x_name].toLowerCase()); });

       var transition = chart.transition().duration(750),
           delay = function(d, i) { return i * 15; };

       transition.selectAll(".bar")
           .delay(delay)
           .attr("x", function(d) { return x0(d[x_name]); });

       transition.select(".x.axis")
           .call(xAxis)
           .selectAll("g")
           .delay(delay)
           .selectAll("text")
             .attr("transform", "translate(-7,0),rotate(-45)")
             .style("text-anchor", "end")
            .delay(delay);

     }
    });
    function type(d) {
      d[y_name] = +d[y_name];
      return d;
    }
}

function mousemove_language_size(d, tip) {
  size = d.size
  unit = " B"
  if(size >= 1024 && size <= 1048576){
      size /= 1024
      unit = " kB"
  }
  else if(size >= 1048577){
      size /= 1048576
      unit = " MB"
  }
  tip
      .text(d.language + ': '+ Math.trunc(size) + unit)
      .style("left", (d3.event.pageX - 78) + "px")
      .style("top", (d3.event.pageY - 12) + "px");
}

function mousemove_language_count(d, tip) {
    count = d.count
    repo = " repositories"
    if (count == 1){
        repo = " repository"
    }
  tip
      .text(d.language + ': ' + count + repo)
      .style("left", (d3.event.pageX - 78) + "px")
      .style("top", (d3.event.pageY - 12) + "px");
}

function mousemove_referrer_count(d, tip){
    count = d.count
    referrals = " referrals"
    if (count == 1.5){
        referrals = " referral"
        count = 1
    }
  tip
      .text(d.referrer + ': ' + count + referrals)
      .style("left", (d3.event.pageX - 130) + "px")
      .style("top", (d3.event.pageY - 12) + "px")
      .style("width", "250px")
      .style("height", "12px");

}

function mousemove_referrer_unique(d, tip){
    uniques = d.uniques
    referrals = " referrals"
    if (uniques == 1.5){
        uniques = 1
        referrals = " referral"
    }
  tip
      .text(d.referrer + ': ' + uniques + referrals)
      .style("left", (d3.event.pageX - 78) + "px")
      .style("top", (d3.event.pageY - 12) + "px")
      .style("width", "250px")
      .style("height", "12px");
}
