<script>
	export let pattern_data;
	export let colorScale;
	export let reloadPlot;
	export let pattern_intervals;
	export let pattern_relations;
	export let highlight;
	import Plotly from '@aknakos/sveltekit-plotly/Plotly.svelte';

	let hovered_pattern = undefined;
	let mouse_x, mouse_y;
	let selected_pattern = '';

	// Format pattern data according to plotly requirements
	let plotlydata = pattern_data.map((pattern, i) => ({
		x: pattern['times'],
		y: [i, i],
		type: 'scatter',
		mode: 'lines',
		name: pattern['id'],
		line: {
			width: 40,
			color: colorScale(pattern['interval'])
		},
		pattern_id: pattern['pattern_id'],
		support: pattern['support'],
		relations: pattern['relations'],
		interval: pattern['interval']
	}));

	// group list by keygetter
	function groupBy(list, keyGetter) {
		const map = new Map();
		list.forEach((item) => {
			const key = keyGetter(item);
			const collection = map.get(key);
			if (!collection) {
				map.set(key, [item]);
			} else {
				collection.push(item);
			}
		});
		return map;
	}

	// update pattern selection on selection or deselection
	function highlightPattern(pattern) {
		console.log('pattern', pattern);
		if (selected_pattern === pattern[0]['pattern_id']) {
			selected_pattern = '';
			pattern_intervals = '';
			pattern_relations = '';
			highlight = '';
		} else {
			selected_pattern = pattern[0]['pattern_id'];
			pattern_intervals = pattern
				.map((d) => [d['interval'], d['x'][0]])
				.sort(function (a, b) {
					return a[1] - b[1];
				})
				.map((e) => e[0]);
			pattern_relations = pattern[0]['relations'];
			console.log(
				'sorterd',
				pattern
					.map((d) => [d['interval'], d['x'][0]])
					.sort(function (a, b) {
						return a[1] - b[1];
					})
					.map((e) => e[0])
			);
		}
		selected_pattern = selected_pattern;
		pattern_intervals = pattern_intervals;
		pattern_relations = pattern_relations;
	}

	// set mouse position and extract pattern on hover
	function handleHover(event, pattern) {
		hovered_pattern = pattern[0]['relations'];
		mouse_x = event.clientX;
		mouse_y = event.clientY;
	}

	// group the data by pattern id
	var groupedBy = groupBy(plotlydata, (e) => e.pattern_id);
	groupedBy = Array.from(groupedBy);

	// set plotly layout
	var layout = {
		height: 110,
		xaxis: {
			showticklabels: false
		},
		yaxis: {
			showgrid: false,
			showline: false,
			showticklabels: false
		},
		margin: {
			l: 20,
			r: 20,
			b: 50,
			t: 10,
			pad: 4
		},
		showlegend: false,
		plot_bgcolor: 'rgba(0,0,0,0)',
		paper_bgcolor: 'rgba(0,0,0,0)'
	};

	// set plotly configuration to static plot
	var config = { staticPlot: true };
</script>

<div class="flex flex-column">
	<div class="w-full">
		<div class="flex flex-row">
			<div class="item w-2/3">
				<p class="font-bold">Pattern</p>
			</div>
			<div class="item w-1/3">
				<p class="font-bold">Support</p>
			</div>
		</div>
		{#each groupedBy as pattern}
			<!-- display each pattern according to the visual representation as in vertTirp (https://doi.org/10.1016/j.eswa.2020.114276), together with the computed support based on querying -->
			<!-- svelte-ignore a11y-mouse-events-have-key-events -->
			<div
				on:mouseover={(event) => handleHover(event, pattern[1])}
				on:mouseout={() => {
					hovered_pattern = undefined;
				}}
				on:click={highlightPattern(pattern[1])}
			>
				<div
					class="flex flex-row pattern"
					style={selected_pattern === pattern[1][0]['pattern_id']
						? 'border-color: gray; border-width: 0.3rem; border-radius: 10px'
						: 'border-color: black;'}
				>
					<div class="item w-2/3">
						<Plotly id="1" data={pattern[1]} {layout} {reloadPlot} {config} />
					</div>
					<div class="item w-1/3">
						<p>{Math.round(pattern[1][0]['support'] * 100) / 100}</p>
					</div>
				</div>
			</div>
		{/each}
	</div>
	<!-- If pattern is hovered, display the symbol sequence (see https://doi.org/10.1016/j.eswa.2020.114276) -->
	{#if hovered_pattern != undefined}
		<div id="tooltip" style="left: {mouse_x}px; top: {mouse_y}px; ">
			<p class="font-bold text-black">
				Sequence {hovered_pattern}
			</p>
		</div>
	{/if}
</div>

<style>
	.pattern {
		pointer-events: all;
	}
	.pattern:hover {
		background-color: rgba(150, 144, 144, 0.491);
		fill-opacity: 0.3;
	}

	.tooltip {
		background-color: '#51617d';
	}
</style>
