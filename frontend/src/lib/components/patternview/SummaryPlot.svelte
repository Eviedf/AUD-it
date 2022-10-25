<script>
	export let summary_data;
	import Plotly from '@aknakos/sveltekit-plotly/Plotly.svelte';
	export let colorScale;
	export let reloadPlot;

	// plotly layout for frequency plot
	var freqlayout = {
		bargap: 0.05,
		height: 250,
		bargroupgap: 0.2,
		title: 'Average frequency',
		yaxis: { title: 'Interval', showticklabels: false },
		margin: {
			l: 100,
			r: 0,
			t: 100
		}
	};

	// plotly layout for duration plot
	var durlayout = {
		height: 250,
		bargap: 0.05,
		bargroupgap: 0.2,
		title: 'Average summed duration (minutes)',
		yaxis: { showticklabels: false },
		margin: {
			l: 50,
			r: 50,
			t: 100
		}
	};

	// format duration data according to plotly requirements
	var durdata = {
		y: summary_data.map((d) => d['value']),
		x: summary_data.map((d) => d['duration']),
		type: 'bar',
		orientation: 'h',
		marker: {
			color: summary_data.map((d) => colorScale(d['value']))
		}
	};

	// format frequency data according to plotly requirements
	var freqdata = {
		y: summary_data.map((d) => d['value']),
		x: summary_data.map((d) => d['frequency']),
		type: 'bar',
		orientation: 'h',
		marker: {
			color: summary_data.map((d) => colorScale(d['value']))
		}
	};
</script>

<div class="flex flex-row">
	<!-- Two plotly components that display frequency and duration bar charts for the selected timeframes, intervals and durations -->
	<div class="item w-1/2">
		<Plotly id="1" data={[freqdata]} layout={freqlayout} bind:reloadPlot />
	</div>

	<div class="item w-1/2">
		<Plotly id="1" data={[durdata]} layout={durlayout} bind:reloadPlot />
	</div>
</div>
