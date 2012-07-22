
/* stats widgets */

var t_fmt = d3.time.format("%I:%M");
var ampm_fmt = d3.time.format("%p");
var day_fmt = d3.time.format("%A");
var date_fmt = d3.time.format("%e %b %Y");
var float_fmt = d3.format(".2f");

function widget_dt(node, date, label) {
    //a datetime widget
    var div = node.append("div").attr("class", "stbox stbox1");
    div.append("div").attr("class", "stlbl1").text(label);
    div.append("div").attr("class", "strow");
    var row = div.append("div").attr("class", "strow");   
    var tmdiv = row.append("div").attr("class", "stval");
    var time = t_fmt(date);
    if (time[0] == "0")
	time = time.substring(1, time.length);
    tmdiv.append("span").text(time);
    tmdiv.append("span").attr("class", "ampm").text(ampm_fmt(date));
    var row = div.append("div").attr("class", "strow")
    row.append("div").attr("class", "stval3").text(day_fmt(date));    
    row.append("div").attr("class", "stval3l").text(date_fmt(date));    
}

function widget_overview(node, date1, date2, subject, label) {
    //a datetime widget
    var div = node.append("div").attr("class", "stbox stbox1");
    div.append("div").attr("class", "stlbl1").text(label);
    div.append("div").attr("class", "strow");
    var row = div.append("div").attr("class", "strow");   
    var tmdiv = row.append("div").attr("class", "stval4");
    var t1 = t_fmt(date1);
    if (t1[0] == "0")
	t1 = t1.substring(1, t1.length);
    tmdiv.append("span").text(t1);
    tmdiv.append("span").attr("class", "ampm2").text(ampm_fmt(date1));

    var t2 = t_fmt(date2);
    if (t2[0] == "0")
	t2 = t2.substring(1, t2.length);
    tmdiv.append("span").text(" - " + t2);
    tmdiv.append("span").attr("class", "ampm2").text(ampm_fmt(date2));
    
    var row = div.append("div").attr("class", "strow");
    row.append("div").attr("class", "stval5").text(date_fmt(date1));    

    if (subject) {
	var row = div.append("div").attr("class", "strow");
	var s = "";
	for (var k in subject) {
	    s+="<div class='stdat'>" + k +": <span style='float:right;'>"+subject[k]+ "</span></div>";
	}
	row.html(s);
    }
}

var ST_PCT = "pct";

function widget_box3(node, data, label, klass) {
    //box holding 3 data vals. data is list of [label, val, color_ind]
    //color_ind is ST_WHITE, ST_YELLOW, ST_GREEN, ...
    // if func, apply it to each datum before display
    if (klass == undefined)
	klass = "stbox1";
    var div = node.append("div").attr("class", "stbox " + klass);
    div.append("div").attr("class", "stlbl1").text(label); 
    div.append("div").attr("class", "strow");
    $.each(data, function(i, item) {
	var lbl = item[0],
	val = item[1],
	klass = "",
	opts = {};
	if (item[2]) 
	    opts = item[2];

	if (val != undefined && val != NaN && opts["type"] == ST_PCT)
	    val = float_fmt(val*100.0);

	if (opts["class"])
	    klass += " " + opts["class"]
	var row = div.append("div").attr("class", "strow");

	row.append("div").attr("class", "stlbl2").text(lbl);

	if (opts["type"] == ST_PCT && val != null && val != NaN && val != "NaN" && val != undefined) {
	    var parts = (val+"").split(".");
	    var div2 = row.append("div").attr("class", "stval2"+klass);
	    div2.append("span").text(parts[0]);
	    div2.append("span").attr("class", "st_pct").text("."+parts[1]);
	    div2.append("span").attr("class", "st_pct").text("%");
	}
	else {
	    if (!val && val!=0)
		val = "NA";
	    row.append("div").attr("class", "stval2"+klass).text(val);
	}
    });
}

var SCORES_DIR = "scores/"; 

var SCORES_LIST = SCORES_DIR + "scores_list.json";

function widget_title(node, title, json) {
    var n = node.append("div").attr("class", "stbox sttitle");
    n.append("a").attr("href", ROOT_URL).attr("class", "tlink").text(title);
    n.append("a").attr("class", "h2_link").attr("href", "README.html").text("About");

    d3.json(SCORES_LIST, function(json) {
	console.log(json);
	if (!json)
	    return;

	n.append("div").attr("class", "h2_link").attr("onclick", "$('#results_select').toggle();$('#case_select').hide();").html("Results History ("+json.length+")");

	var sel = d3.select("body").append("div")
	    .attr("id", "results_select").attr("class", "tr_select")

	sel.selectAll("div")
	    .data(json)
	    .enter()
	    .append("div").attr("class", "sel_row")
	    .append("span")
	    .attr("class", function (item) {
		if (item == curr_res_fname)
		    return "sel_a selected";
		else
		    return "sel_a";
	    })
	    .attr("onclick", function (item) {
		return '$("#results_select").hide();viz_file("'+item+'");';
	    })
	    .html(function (item) {
		return item
	    })
    });

    var sel = d3.select("body").append("div")
	.attr("id", "case_select").attr("class", "tr_select")

    var baseurl = document.URL.substring(0, document.URL.lastIndexOf("#"));
    sel.selectAll("div")
	.data(json.results)
	.enter()
	.append("div").attr("class", "sel_row")
	.append("a").attr("class", "sel_a")
	.attr("href", function(item){return baseurl+"#case_"+case_id(item)})
	.attr("onclick", '$("#case_select").hide()')
	.html(function (item) {return item.labels_file + " --> "+item.recognizer});

    n.append("div").attr("class", "h2_link").attr("onclick", "$('#case_select').toggle();$('#results_select').hide();").html("Test Cases ("+json.results.length+")");

    node.append("div").attr("style", "clear:both;");
}

function widget_h2(node, title, id) {
    var n = node.append("div").attr("class", "stbox sttitle")
    if (id) {
	n.attr("id", id);
    }
    n.html(title)
	.append("a").attr("class", "h2_link").attr("href", "#top").text("Top");
    node.append("div").attr("style", "clear:both;");
}

function pie_chart(node, data, title) {
    if (!data)
	return;

    //create pie chart from data and add to node
    var w = 260,
    r = 65, //radius
    rd = r + 2, //to translate
    h = r*2 + 4,
    leg_yoff = 8, //y offset legend
    leg_x_off = 8,
    box_h = 18; //legend color box

    var data = [d3.entries(data)];

    node = node.append("div").attr("class", "stbox st_pie2");

    node.append("div").attr("class", "stlblpie").text(title);    

    var vis = node.append("svg:svg")
	.data(data)
	.attr("width", w).attr("height", h).append("svg:g")
        .attr("transform", "translate(" + rd + "," + rd + ")")

    var arc = d3.svg.arc()
        .outerRadius(r);

    var pie = d3.layout.pie()
        .value(function(d) { return d.value; });

    var arcs = vis.selectAll("g.slice")
        .data(pie)
        .enter()
        .append("svg:g")
        .attr("class", "slice");

    arcs.append("svg:path")
        .attr("fill", function(d, i) { return pie_colors[d.data.key]; } ) //slice color
	.attr("class", "pie_path")
	.attr("d", arc);                                   

    arcs.append("svg:rect")
	.attr("class", "legend_color")
	.attr("width", box_h)
	.attr("height", box_h)
        .attr("fill", function(d, i) { return pie_colors[d.data.key]; } )
	.attr("y", function(d, i) { return i*(box_h + 4) - r + leg_yoff;})
	.attr("x", r + 18);

    arcs.append("svg:text")
	.attr("class", "legend_text")
        .text(function(d, i) { return d.data.key; }) 
	.attr("y", function(d, i) { return i*(box_h + 4) - r  + leg_yoff + 14;})
	.attr("x", r + box_h + 24);

    arcs.append("svg:text")
	.attr("class", "legend_val")
        .text(function(d, i) { return (d.data.value*100.0).toFixed(1) + " %"; }) 
	.attr("y", function(d, i) { return i*(box_h + 4) - r  + leg_yoff + 14;})
	.attr("x", r + box_h + 52);

}

var pie_colors = { //score color
    "TPr": "#77AB13",
    "C": "#77AB13",
    "TNr": "#77AB13",
    "Usr": "#fdd0a2",
    "Uer": "#fdae6b",
    "Osr": "#fdd0a2",
    "Oer": "#fdae6b",
    "I'": "#AE432E",
    "Ir": "#AE432E",
    "Dr": "#AE432E",
    "D": "#AE432E",
    "Fr": "#B5712E",
    "F": "#B5712E",
    "F'": "#B5712E",
    "Mr": "#B5712E",
    "M'": "#fdd0a2",
    "M": "#fdd0a2",
    "FM": "#fdae6b",
    "FM'": "#fdae6b",
}

var lbl_conv = {
    "Usr": "U\u03C9r",
    "Uer": "U\u03B1r",
    "Osr": "O\u03C9r",
    "Oer": "U\u03B1r",
    "Usr": "U\u03C9r",
    "Uer": "U\u03B1r",
}

function convert_label(lbl) {
    if (lbl_conv[lbl])
	return lbl_conv[lbl];
    else
	return lbl;
}

function interval_chart(node, data, x, klass, y_off, id) {
    //create an time interval chart from the data and add to node. id refers to interval detail elem
    node.append("svg:g")
	.attr("class", klass)
	.selectAll("rect")
	.data(data)
	.enter().append("svg:rect")
	.attr("style", function(d) {
	    if (klass=="segment_chart" && (d["score"] == "TP" || d["score"] == "TN") ) { return "stroke:#343738;fill: #77AB13;"};
	})
	.attr("rx", 2).attr("ry", 2)
	.attr("y", y_off)
	.attr("x", function(d, i) { return x_offset + x(d["t1"]); })
	.attr("width", function(d, i) { if((x(d["t2"]) - x(d["t1"])) < 0)console.log(d);return x(d["t2"]) - x(d["t1"]); })
	.attr("height", bar_h)
	.on("mouseover", function(d) { interval_detail(d, klass, id); })
	.on("mouseout", function(d) { d3.select("#"+id).text(""); } );

}

function interval_detail(d, klass, id) {
    //show detail of this interval
    var s = tms_fmt(new Date(d["t1"])) + " - " + tms_fmt(new Date(d["t2"]));
    if (klass == "truth_chart")
	s += " (Ground truth) - " + d.label;
    else if (klass == "detected_chart")
	s += " (Detected) - " + d.label;
    else if (klass == "segment_chart") {
	s += " (Segment " + d["score"] + ") ";
	if (d["err"])
	    s += " " + d["err"]
    }
    d3.select("#"+id).text(s);
}

var temps_blue = ["#F0F9E8", "#CCEBC5", "#A8DDB5", "#7BCCC4", "#43A2CA", "#0868AC"];

function heat_test(node) {
    var temps = ["ff0000", "ff6600", "ffcc00", "ffff00", "ccff00", "99ff00", "66ff00", "00ff00", "00ff66", "00ffcc", "00ccff", "0099ff"];
    $.each(temps, function(i, v) {
	node.append("div").attr("style", "background-color:#" + v).text(v);
    });
}

function data_table(node, title, data, type) {
    //make a table out of data name-val pairs. if pct, show val as percentage
    var data_tbl = node.append("div").attr("class", "stbox sttbl");
    data_tbl.append("div").attr("class", "data_tbl_head").text(title);

    var keys = d3.keys(data); 
    keys.sort()

    $.each(keys, function(index, value) {
	var data_row = data_tbl.append("div").attr("class", "data_row");
	data_row.append("span").attr("class", "data_lbl").text(value+":");
	var val;
	if (type == "pct")
	    val = (data[value]*100.0).toFixed(2) + " %"
	else if (type == "int")
	    val = d3.round(data[value], 2)
	else
	    val = data[value];
	data_row.append("span").attr("class", "data_val").text(val);
    });
}

function ead_chart(node, t, d) {
    var width = 1110,
    height = 85,
    bar_h = 32,
    y_off = 0;

    var xmax = t["D"] + t["F"] + t["M"] + t["FM"] 
	+ d["I'"] + d["M'"] + d["F'"] + d["FM'"] + d["C"];

    var x = d3.scale.linear()
	.domain([0, xmax])
	.range([0, width]);
    
    var correct_events = d["C"];
    var actual_events = t["D"] + t["F"] + t["FM"] + t["M"] + correct_events;
    var returned_events = correct_events + d["M'"] + d["FM'"] + d["F'"] + d["I'"];

    var node = node.append("div").attr("class", "stead");
    node.append("div").attr("class", "stlblead").text("Event analysis diagram"); 

    var ead = node.append("svg:svg")
	.attr("width", width)
	.attr("height", height)
    
    ead = ead.append("svg:g");
    
    // add the rectangles and labels for each error type
    ead_box(ead, 0, x(t["D"]), "ead_D", "D:"+t["D"], bar_h);
    ead_box(ead, x(t["D"]), x(t["F"]), "ead_F", "F:"+ t["F"], bar_h);
    ead_box(ead, x(t["D"] + t["F"]), x(t["FM"]), "ead_FM", "FM:"+t["FM"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"]), x(t["M"]), "ead_M", "M:" + t["M"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"] + t["M"]), x(d["C"]), "ead_C", "C:"+d["C"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"] + t["M"] + d["C"]), x(d["M'"]), "ead_M", "M':"+d["M'"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"] + t["M"] + d["C"] + d["M'"]), x(d["FM'"]), "ead_FM", "FM':"+d["FM'"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"] + t["M"] + d["C"] + d["M'"] + d["FM'"]), x(d["F'"]), "ead_F", "F':"+d["F'"], bar_h);
    ead_box(ead, x(t["D"] + t["F"] + t["FM"] + t["M"] + d["C"] + d["M'"] + d["FM'"] + d["F'"]), x(d["I'"]), "ead_I", "I':"+d["I'"], bar_h);
    
    event_line(ead, x(actual_events - correct_events), x(actual_events+returned_events-correct_events), 0, "Detected (total="+returned_events+")", width-100, -8);
    event_line(ead, 0, x(actual_events), bar_h, "Truth (total=" + actual_events + ")", 12, bar_h+18);
}

function event_line(node, start, end, y, label, label_x, label_y) {
    //add line for actual events
    node.append("svg:line")
	.attr("x1", start)
	.attr("x2", end)
	.attr("y1", y)
	.attr("y2", y)
	.attr("stroke", "#ddd")
	.attr("stroke-width", "2px");

    node.append("svg:text")
	.attr("class", "event_lbl")
	.attr("x", label_x)
	.attr("y", label_y)
	.attr("text-anchor", "left")
	.text(label);
}

function ead_box(node, x, w, klass, lbl, bar_h) {
    pad_y = 12;
    if (!w)
	return;
    node.attr("transform", "translate(0,20)")
	.append("svg:rect")
	.attr("class", "ead "+klass)
	.attr("x", x)
	.attr("width", w)
	.attr("height", bar_h)

    node.append("svg:text")
	.attr("class", "ead_lbl")
	.attr("x", x + 6)
	.attr("y", bar_h/2 + 5 )
	.text(lbl)
}


function samples_chart(node, data, x, title) {
    //shows the times of various samples
    var div = node.append("div").attr("class", "stbox");
    var chart = div.append("svg:svg")
	.attr("width", width+(x_offset*2)+x_pad)
	.attr("height", 16)
	.append("svg:g")

    var y_off = 0;
    var line_w = 1;

    chart.append("svg:g")
	.attr("class", "samples_chart")
	.selectAll("line")
	.data(data)
	.enter().append("svg:line")
	.attr("y1", 0)
	.attr("y2", 32)
	.attr("x1", function(d, i) {return x_offset + x(Date.parse(d)); })
	.attr("x2", function(d, i) {return x_offset + x(Date.parse(d)); })

    div.append("div")
	.attr("style", "text-align:center;font-size:11px;;padding-top:6px;")
	.html(title)

}

function ti_chart(node, data, x, title) {
    //time interval chart
    var div = node.append("div").attr("class", "stbox");
    var chart = div.append("svg:svg")
	.attr("width", width+(x_offset*2)+x_pad)
	.attr("height", 16)

    var y_off = 0;
    var line_w = 1;

    data = $.map(data.intervals, function(item, i) { return {"t1":Date.parse(item.t1), "t2":Date.parse(item.t2) } });

    chart.append("svg:g")
	.attr("class", "ti_chart")
	.selectAll("rect")
	.data(data)
	.enter().append("svg:rect")
	.attr("rx", 2)
	.attr("ry", 2)
	.attr("y", y_off)
	.attr("x", function(d, i) { return x_offset + x(d["t1"]); })
	.attr("width", function(d, i) { if((x(d["t2"]) - x(d["t1"])) < 0)console.log(d);return x(d["t2"]) - x(d["t1"]); })
	.attr("height", 16);

    div.append("div")
	.attr("style", "text-align:center;font-size:11px;;padding-top:6px;")
	.html(title);
}
