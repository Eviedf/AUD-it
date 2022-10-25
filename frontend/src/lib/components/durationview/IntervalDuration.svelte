<script>
	import { scale } from 'svelte/transition';
	export let dur_data;
	import Plotly from '@aknakos/sveltekit-plotly/Plotly.svelte';
	export let selecteddurs;
	export let reloadPlot;
	export let color;

	let today = new Date();
	let reduced = calculatereduced(dur_data);
	today = today.setHours(0, 0, 0, 0);
	$: reloadPlot = reloadPlot;
	$: dur_data = dur_data;
	let trace;

	// converts hex code to rgb color code
	function hextorgb(hex) {
		hex = hex.substring(1);
		var bigint = parseInt(hex, 16);
		var r = (bigint >> 16) & 255;
		var g = (bigint >> 8) & 255;
		var b = bigint & 255;
		return 'rgb(' + r + ',' + g + ',' + b + ')';
	}

	$: reduced = calculatereduced(dur_data);

	// Compute the total duration
	function calculatereduced(dur_data) {
		console.log(dur_data);
		if (!dur_data) {
			console.error('DurData in undefined');
			return;
		}
		return dur_data.reduce((i, j) => {
			i[j.duration] = (i[j.duration] || 0) + 1;
			return i;
		}, {});
	}

	// Compute the data, formatted according to plotly requirements
	$: if (color) {
		trace = {
			x: Object.keys(reduced),
			y: Object.values(reduced),
			type: 'bar',
			interval: dur_data[0]['value'],
			marker: { color: hextorgb(color) }
		};
	}

	// Set plotly layout
	var layout = {
		bargap: 0.05,
		barwidth: 1,
		// width: 500,
		height: screen.height * 0.2,
		xaxis: { title: 'Minutes' },
		yaxis: { title: 'log(Count)', type: 'log', autorange: true },
		margin: {
			l: 50,
			r: 20,
			b: 50,
			t: 50,
			pad: 5
		}
	};

	// Set plotly configuration
	var config = {
		modeBarButtonsToRemove: ['toImage', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'pan2d']
	};

	// Select durations with selection box
	function onSelected(d, interval) {
		interval = interval.replaceAll('/', '-');
		if (d) {
			console.log('selecteddata', d);
			selecteddurs[interval] = d.range.x;
		} else {
			delete selecteddurs[interval];
			selecteddurs = selecteddurs;
			console.log('empty selection', selecteddurs);
		}
	}
</script>

<div class="flex flex-col">
	<div class="ml-3" transition:scale>
		<!-- Plotly barchart with durations -->
		<Plotly
			id="1"
			data={[trace]}
			{layout}
			on:selected={(data) => onSelected(data.detail, trace.interval)}
			bind:reloadPlot
			{config}
		/>
	</div>
</div>
