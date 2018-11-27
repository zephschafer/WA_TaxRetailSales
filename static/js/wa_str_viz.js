d3.csv("static/data/SalTaxRev_WA_state_N0_annl.csv", function(data) {
  var dataset = data;
  var sales = [];
  var units = []
  var date = [];
  data.map(function(d) {
      sales.push(+d.sales);
      units.push(d.unit);
      date.push(d.date);
  })
  var w = 600;
  var h = 400;
  var barPadding = 2;
  var hPadding = 20
  var svg = d3.select("#chart-holder")
              .append("svg")
              .attr("width",w)
              .attr("height",h);
  var xScale = d3.scale.ordinal()
                  .domain(d3.range(sales.length))
                  .rangeRoundBands([0,w], 0.05);
  var yScale = d3.scale.linear()
                .domain([0, d3.max(sales, function(d) { return d; })])
                .range([0, h - hPadding]);
  svg.selectAll("rect")
      .data(sales)
      .enter()
      .append("rect")
        .attr({
          "x": function(d,i) { return xScale(i);},
          "y": function(d) { return h - yScale(d) ;},
          "width": (w / sales.length - barPadding),
          "height": function(d) { return  d ;} ,
          "fill": function(d) {return "rgb(0,0,"  + yScale(d)/2.5 + ")";}
        })
      .on("mouseover", function(d) { d3.select(this)
        .attr("fill", "rgb(254, 187, 98)");
        var xPosition = parseFloat(d3.select(this).attr("x")) + xScale.rangeBand() / 2;
        var yPosition = parseFloat(d3.select(this).attr("y")) + 14 ;
        d3.select("#tooltip")
            .style("left", (xPosition + 100) + "px")
            .style("top", (yPosition + 100) + "px")
            .select("#value")
            .text("$" + d3.round(d/(10**9)) + "B");
        d3.select("#tooltip").classed("hidden", false);
        })
      .on("mouseout", function(d) {
        d3.select("#tooltip").classed("hidden", true)
        d3.select(this)
        .transition()
        .duration(300)
          .attr({
          "fill": function(d) {return "rgb(0,0,"  + yScale(d)/2.5 + ")";}
          })
          });
  svg.selectAll("text")
      .data(date)
      .enter()
      .append("text")
      .text(function(d) {return d;})
      .attr({
        "x":function(d,i) {return xScale(i) + (w/date.length - barPadding)/2 ;},
        "y":function(d,i) {return h - yScale(d) - 14 ;},
        "font-family":"sans-serif",
        "font-size":"12px",
        "fill":"white",
        "text-anchor":"middle"
      });
});
