

//_____1_1_DEFINE_DATA
d3.csv("static/data/STR_WA_C_N1_A_W.csv", function(data) {

  var data = data;
  // Set Initial Geography
  var countyselection = "Statewide"
  drawViz(data, countyselection)

});


  //______2_DEFINE_CHARTHOLDER
var margin = {top: 20, right: 160, bottom: 35, left: 30};
var width = 600 - margin.left - margin.right;
var height = 400 - margin.top - margin.bottom;
var svg = d3.select("#stacked-chart")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
var parse = d3.time.format("%m/%d/%y").parse;


//_____3_DRAW_VIZ
var drawViz = function(data, countyselection) {
  //______3_1_DEFINE_DATA
  var countyDim = crossfilter(data).dimension(function(d) {return d.county;});
  var countyFilter = countyDim.filter(countyselection).top(Infinity);
  var countyList = d3.nest().key(function(d) {return d.county;}).entries(data).map(function(d) {return d.key;});
  console.log(countyFilter);
  var industryList = d3.keys(data[1])
  industryList.splice(0,2);
  countyFilter.sort(function(x, y){
     return d3.ascending(parse(x.year), parse(y.year));
  })
  var dataset = d3.layout
    .stack()(industryList
    .map(function(naics,i) {
    return countyFilter.map(function(d) {
      return {x: parse(d.year), y: +d[naics], z:industryList[i]};
    });
    }));
  //______3_2_DEFINE_AXES
  var xScale = d3.scale.ordinal()
    .domain(countyFilter.map(function(d) { return parse(d.year); }))
    .rangeRoundBands([10, width-10], 0.02);

  var xAxis = d3.svg.axis()
    .scale(xScale)
    .orient("bottom")
    .tickFormat(d3.time.format("%Y"));

  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis);

  var yScale = d3.scale.linear()
    .domain([0, d3.max(dataset, function(d) {  return d3.max(d, function(d) { return d.y0 + d.y; });  })])
    .range([height, 0]);

  var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient("left")
    .ticks(5)
    .tickSize(-width, 0, 0)
    .tickFormat( function(d) { return "$" + d/(10**9) + "B" } );

  var yAxisUpdate = svg.append("g")
    .attr("class", "y axis")
    .call(yAxis);

  yAxisUpdate.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 6)
    .attr("dy",".71em")
    .style("text-anchor","end");

  //______3_3_DEFINE_COLORS
  var colors = d3.scale.linear()
    .domain([0,d3.max(dataset, function(d, i) {  return i; })])
    .interpolate(d3.interpolateHcl)
    .range([d3.rgb("#533B95"), d3.rgb('#98B59F')]);

  //______3_4_DEFINE_BARS
  var updateBars = function(dataset) {
    // Reset y-scale
    yScale.domain([0, d3.max(dataset, function(d) {  return d3.max(d, function(d) { return d.y0 + d.y; });  })]);
    yAxisUpdate.call(yAxis);

    // Based on other D3 examples such as below
    // e.g. <http://bl.ocks.org/williaster/10ef968ccfdc71c30ef8>,
    // I should probably using "_exit().remove()"
    // But I had trouble when calling that on the bars var below"
    d3.selectAll("rect").remove();

    var bars = svg.selectAll("bars")
      .data(dataset)
      .enter()
        .append("g")
        .style("fill", function(d,i) { return colors(i);})
        .selectAll("rect")
        .data(function(d) {return d;});
    bars.enter()
      .append("rect")
      .attr({
        "x" : function(d) { return xScale(d.x); },
        "y" : function(d) { return yScale(d.y0 + d.y); },
        "height" : function(d) { return yScale(d.y0) - yScale(d.y0 + d.y); },
        "width" : xScale.rangeBand()
      })
      .on("mouseover", function() { tooltip.style("display", null); })
      .on("mouseout", function() { tooltip.style("display", "none"); })
      .on("mousemove", function(d,i) {
        var xPosition = d3.mouse(this)[0] - 15;
        var yPosition = d3.mouse(this)[1] - 25;
        tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")");
        tooltip.select("text")
          .text("" + d.z + " $" + d3.round(d.y/(10**9)) + "B");
      });

    //______3_5_DEFINE_TOOLTIPS
    var tooltip = svg.append("g")
      .attr("class", "tooltip")
      .style("display", "none");
    tooltip.append("rect")
      .attr({
        "width" : 30,
        "height" : 20,
        "fill" : "white"
      })
      .style("opacity", 0.5);
    tooltip.append("text")
      .attr({
        "x" : 15,
        "dy" : "1.2em"
        })
      .style("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("font-weight", "bold");

  //______3_6_DEFINE_TOOLTIPS
  // Not active. Unsure why.
  // Again probably to do with my messy definition of bars
  bars
    .transition().duration(250)
    .attr({
      "y" : function(d) { return yScale(d.y0 + d.y); },
      "height" : function(d) { return yScale(d.y0) - yScale(d.y0 + d.y); },
    })

  d3.selectAll(".legend").remove();

  //______3_7_DEFINE_LEGEND
  var legend = svg.selectAll(".legend")
    .data(industryList)
    .enter()
      .append("g")
      .attr({
        "class": "legend",
        "transform": function(d, i) { return "translate(30," + i * 19 + ")"; }
      });
  legend.append("rect")
    .attr()
    .attr({
      "x": width - 18,
      "width": 18,
      "height": 18
    })
    .style("fill", function(d, i) {return colors(i);});
  legend.append("text")
    .attr({
      "x": width + 5,
      "y": 9,
      "dy" : ".35em",
    })
    .style("text-anchor", "start")
    .text(function(d) { return d ;});
  };


  //_____3_8_DEFINE_DROPDOWNCHANGES
  var updateData = function() {
		var newCounty = d3.select(this)
                  .property("value");
    var countyDim = crossfilter(data).dimension(function(d) {return d.county;});
    var countyFilter = countyDim.filter(newCounty).top(Infinity);
    var countyList = d3.nest().key(function(d) {return d.county;}).entries(data).map(function(d) {return d.key;});
    console.log(countyFilter);
    var industryList = d3.keys(data[1])
    industryList.splice(0,2);
    countyFilter.sort(function(x, y){
       return d3.ascending(parse(x.year), parse(y.year));
    })
    var newData = d3.layout
      .stack()(industryList
      .map(function(naics,i) {
      return countyFilter.map(function(d) {
        return {x: parse(d.year), y: +d[naics], z:industryList[i]};
      });
      }));

    updateBars(newData);
  };

  //______3_6_APPLY_DROPDOWNS
  var countyselect = d3.select("#county-select")
    .insert("select", "svg")
    .on("change", updateData);

  countyselect.selectAll("option")
    .data(countyList)
    .enter()
      .append("option")
      .attr("value", function(d) {return d})
      .html(function(d){ return d; });

  // // Below is an incomplete addition of an industry filter
  // // it will require
  // // (1) using the dropdown to select specific columns
  // // ... (as the data is currently arranged wide along industry)
  // // (2) re-arranging the data completely and applying an additional crosfilter
  // // ... var industryselect = d3.select("#industry-select") .insert("select", "svg")
  //
  // industryselect.selectAll("option")
  //   .data(industryList)
  //   .enter()
  //   .append("option")
  //   .attr("value", function(d) {return d})
  //   .html(function(d){ return d; });
  //

    updateBars(dataset);


};
