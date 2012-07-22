
/* TODO
- TZ indicator in dt widget.
*/

SCORES_FILE = SCORES_DIR + "scores.json";
ROOT_URL = "/"

d3.json(SCORES_FILE, function(json) {
    viz(json, SCORES_FILE); 
});


if (document.URL.lastIndexOf("#") != -1) {
    var baseurl = document.URL.substring(0, document.URL.lastIndexOf("#"));
    window.location = baseurl + "#" + document.URL.substring(document.URL.lastIndexOf("#")+1, document.URL.length);
}


function isInteger(f) {return typeof(f)==="number" && Math.round(f) == f;}
function isFloat(f) { return typeof(f)==="number" && !isInteger(f); }

var float_fmt = d3.format(".2f");
var int_fmt = d3.format(".1f");

function viz_file(f) {
    console.log(f);
    d3.json(ROOT_URL+f, function(json) {
	viz(json, f); 
    });
}

var case_num = 0; //numbering cases 1-N

var curr_res_fname;

function viz(json, fname) {
    curr_res_fname = fname;

    //reset the view
    d3.select("body").html("");
    case_num = 0;

    console.log(json);
    if (json==null||json==undefined) {
	widget_title(d3.select("body"),"No results found");
	return;
    }
    
    //viz the result object
    var test_time = d3.time.format("%Y-%m-%dT%H:%M:%S").parse(json.t.substring(0, 19)); //strips the fractional seconds

    var title = "Performance Results: " + test_time;
    d3.select("html").append("title").text(title);

    var body = d3.select("body");
    body.append("a").attr("name", "top") 

    widget_title(body, "Performance Overview", json);    

    var div = body.append("div").attr("class", "brow ssect");

    //Date time box showing the time of the test run
    widget_dt(div, test_time, "Test Time");

    //stats about number of test cases, truths, and detected
    widget_box3(div, [ ["Cases", json.results.length], ["Truths", json.stats.truth_count], ["Detected", json.stats.detected_count] ], "Test Cases", "stbox2");

    var frsc = json.scores.frame_scores;

    var div = body.append("div").attr("class", "brow");

    //a box of positive frame stats
    widget_box3(div, [ 
	["Deletion", frsc.p_rates.Dr,  {"class":"st_red", "type":ST_PCT}],
	["Timing errors", frsc.p_rates.Uer + frsc.p_rates.Usr + frsc.p_rates.Fr, {"class":"st_yellow", "type":ST_PCT}],
	["True positive", frsc.p_rates.TPr, {"class":"st_green", "type":ST_PCT}] 
    ], "Positive frames (" + (100.0*frsc.p_rate).toFixed(1)+ "%)", "stbox3");

    // negative frame stats
    widget_box3(div, [ 
	["Insertion", frsc.n_rates.Ir, {"class":"st_red", "type":ST_PCT}],
	["Timing errors", frsc.n_rates.Oer + frsc.n_rates.Osr + frsc.n_rates.Mr, {"class":"st_yellow", "type":ST_PCT}],
	["True negative", frsc.n_rates.TNr, {"class":"st_green", "type":ST_PCT}],
    ], "Negative frames (" + (100.0*frsc.n_rate).toFixed(1)+ "%)", "stbox3");

    var esc = json.scores.event_scores;

    // truth events
    widget_box3(div, [ 
	["Deletion", esc.t_rates.D,  {"class":"st_red", "type":ST_PCT}],
	["Split / Merged", esc.t_rates.F + esc.t_rates.FM + esc.t_rates.M, {"class":"st_yellow", "type":ST_PCT}],
	["Correct", esc.t_rates.C, {"class":"st_green", "type":ST_PCT}],
    ], "Truth events (" + json.stats.truth_count + ")", "stbox3");

    //detected events
    widget_box3(div, [ 
	["Insertion", esc.d_rates["I'"],  {"class":"st_red", "type":ST_PCT}],
	["Split / Merged", esc.d_rates["F'"] + esc.d_rates["FM'"] + esc.d_rates["M'"], {"class":"st_yellow", "type":ST_PCT}],
	["Correct", esc.d_rates.C, {"class":"st_green", "type":ST_PCT}],
    ], "Detection events (" + json.stats.detected_count + ")", "stbox3");
    
    //data_table(body, "Frame counts", frsc.frame_counts);

    var div = body.append("div").attr("class", "brow");
    if (frsc.p_rate != 0) 
	pie_chart(div, frsc.p_rates, "Positive frames (" + pct_str(frsc.p_rate) + ")");

    if (frsc.n_rate != 0) 
	pie_chart(div, frsc.n_rates, "Negative frames (" + pct_str(frsc.n_rate) +")");

    var div = body.append("div").attr("class", "brow");
    pie_chart(div, esc.t_rates, "Truth events (" + json.stats.truth_count + ")");

    if (json.stats.detected_count)
	pie_chart(div, esc.d_rates, "Detected events (" + json.stats.detected_count + ")");

    body.append("div").attr("style", "clear:both;padding:24px;");

    $.each(json.results, function(index, value) {
	result_details(value);
    });

    body.append("div").attr("style", "clear:both;padding:0px 12px;color:#ccc;font-size:12px;margin-bottom:24px;").html("For a description of the metrics used here, see:<br/><br/>[1] <b>Ward, J. A., Lukowicz, P., & Gellersen, H. W. (2011). Performance metrics for activity recognition.</b> ACM Transactions on Intelligent Systems and Technology (TIST), 2(1), 1-23. doi:10.1145/1889681.1889687. <a style='font-size:smaller' href='http://gtubicomp.pbworks.com/w/file/fetch/48480476/Ward2011-Performance%20metrics%20for%20activity%20recognition.pdf'>[PDF]</a>");

    body.append("p").attr("class", "footer").text("");
}

function pct_str(dec) {
    return (dec*100.0).toFixed(2) + "%";
}

var width = 1082,
bar_h = 24,
bar_pad = 6,
label_pad = 32,
x_offset = 24,
x_pad = 0;

var height = 3*bar_h + 3*bar_pad + label_pad;

var tm_fmt = d3.time.format("%I:%M %p");
var tms_fmt = d3.time.format("%I:%M:%S %p");

var ISO_FMT = d3.time.format("%Y-%m-%dT%H:%M:%S");

function parse_isotime(isotime) {
    return ISO_FMT.parse(isotime.substring(0, 19)); //strips the fractional seconds
}

function addNums(l) {
    var r = 0.0;
    $.each(l, function(i) { r += (isNaN(l[i]) ? 0: l[i]) });
    return r;
}

function case_id(result) {
    return (result.labels_file+"__to__"+result.recognizer).replace(/\W/g, "_"); //use path as id, remove non-word chars
}

function result_details(result) {
    //visualize the detection result
    case_num += 1;
    var body = d3.select("body");
    var detail_id = "detail_"+case_id(result);

    widget_h2(body, "Case " + case_num + ": &nbsp;<code>"+result.labels_file  +" --> " + result.recognizer + "</code>", "case_"+case_id(result));

    var div = body.append("div").attr("class", "brow ssect");

    if (result.labels.length > 0)
	widget_overview(div, parse_isotime(result.labels[0].t1), parse_isotime(result.labels[result.labels.length-1].t2), result.subject, "Overview");

    widget_box3(div, [ ["Labels", result.labels.length], ["Detected", result.detected.length], ["Segments", result.scores.segments.length] ], "Test Cases", "stbox2");

    var fsc = result.scores.frame_score;

    var div = body.append("div").attr("class", "brow");
    widget_box3(div, [
	["Deletion", fsc.p_rates.Dr,  {"class":"st_red", "type":ST_PCT}],
	["Timing errors", fsc.p_rates.Uer + fsc.p_rates.Usr + fsc.p_rates.Fr, {"class":"st_yellow", "type":ST_PCT}],
	["True positive", fsc.p_rates.TPr, {"class":"st_green", "type":ST_PCT}], 
    ], "Positive frames (" + pct_str(fsc.p_rate) + ")", "stbox3");

    widget_box3(div, [
	["Insertion", fsc.n_rates.Ir, {"class":"st_red", "type":ST_PCT}],
	["Timing errors", addNums([fsc.n_rates.Osr, fsc.n_rates.Oer, fsc.n_rates.Mr]), {"class":"st_yellow", "type":ST_PCT}],
	["True negative", fsc.n_rates.TNr, {"class":"st_green", "type":ST_PCT}], 
    ], "Negative frames (" + pct_str(fsc.n_rate) + ")", "stbox3");

    var esc = result.scores.events;

    widget_box3(div, [
	["Deletion", esc.t_rates.D, {"class":"st_red", "type":ST_PCT}],
	["Split / Merged", esc.t_rates.F + esc.t_rates.M + esc.t_rates.FM, {"class":"st_yellow", "type":ST_PCT}],
	["Correct", esc.t_rates.C, {"class":"st_green", "type":ST_PCT}], 
    ], "Truth events (" + result.labels.length  + ")", "stbox3");

    widget_box3(div, [
	["Insertion", esc.d_rates["I'"], {"class":"st_red", "type":ST_PCT}],
	["Split / Merged", esc.d_rates["F'"] + esc.d_rates["M'"] + esc.d_rates["FM'"], {"class":"st_yellow", "type":ST_PCT}],
	["Correct", esc.d_rates["C"], {"class":"st_green", "type":ST_PCT}], 
    ], "Detected events (" + result.detected.length  + ")", "stbox3");

    body.append("div").attr("style", "clear:both;");

    var truth_times = $.map(result.labels, function(item, i) { return {"t1":Date.parse(item.t1), "t2":Date.parse(item.t2), "label":item.label}; });
    var detected_times = $.map(result.detected, function(item, i) { return {"t1":Date.parse(item.t1), "t2":Date.parse(item.t2), "label":item.label}; });
    var segments = $.map(result.scores.segments, function(item, i) { return {"t1":Date.parse(item.t1), "t2":Date.parse(item.t2), "err":item.err, "score":item.score}; });

    if (segments.length > 0) {
	var x = d3.time.scale()
	    .domain([segments[0]["t1"], segments[segments.length-1]["t2"]])
	    .range([0, width]);

	var xticks = x.ticks(12);

	var div = body.append("div").attr("class", "stbox st_interval_box");
	div.append("div").attr("id", detail_id).attr("class", "item_detail");

	var chart = div.append("svg:svg")
	    .attr("width", width+(x_offset*2)+x_pad)
	    .attr("height", height)
	    .append("svg:g")

	chart.selectAll("line")
	    .data(xticks)
	    .enter().append("svg:line")
	    .attr("x1", function(d) { return x(d) + x_offset; } )
	    .attr("x2", function(d) { return x(d) + x_offset; } )
	    .attr("y1", 0)
	    .attr("y2", height-18)
	    .attr("stroke", "#555");
	
	interval_chart(chart, truth_times, x, "truth_chart", bar_pad, detail_id);
	interval_chart(chart, detected_times, x, "detected_chart", bar_h + 2*bar_pad, detail_id);
	interval_chart(chart, segments, x, "segment_chart", bar_h*2 + 3*bar_pad, detail_id);
	
	chart.selectAll(".xlabel")
	    .data(xticks)
	    .enter().append("svg:text")
	    .attr("class", "xlabel")
	    .text(function(d) { return tm_fmt(new Date(d)); })
	    .attr("x", function(d) { return x_offset + x(d) })
	    .attr("y", height-4)
	    .attr("text-anchor", "middle");
    }

    if (result.sample_intervals != undefined) {
	var tdiff = segments[segments.length-1]["t2"] - segments[0]["t1"];
	$.each(result.sample_intervals, function(i, v) {
	    var count = result.sample_intervals[i].count;
	    var s = "<b>"+i+"</b>"+ " | count: " + count  + " | rate: " + int_fmt(tdiff/1000/count) + "s " ; 
	    ti_chart(body, v, x, s);	    
	});
    }

    body.append("div").attr("style", "clear:both;");

    var div = body.append("div").attr("class", "brow");

    var tot_frames = fsc.frame_counts.P + fsc.frame_counts.N;
    
    if (fsc.frame_counts.P) {
	pie_chart(div, fsc.p_rates, "Positive frames (" + pct_str(fsc.p_rate) + ")");
    }

    if (fsc.frame_counts.N) {
	pie_chart(div, fsc.n_rates, "Negative frames (" + pct_str(fsc.n_rate) + ")");
    }

    var div = body.append("div").attr("class", "brow");

    if (result.labels.length > 0)
	pie_chart(div, esc.t_rates, "Truth events (" + result.labels.length + ")");

    if (result.detected.length > 0)
	pie_chart(div, esc.d_rates, "Detected events (" + result.detected.length + ")");

    var div = body.append("div").attr("class", "brow ead");
    ead_chart(div, result.scores.events.t_counts, result.scores.events.d_counts);

    body.append("div").attr("style", "clear:both;padding:24px;");
}

