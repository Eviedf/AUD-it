<script>
	// @ts-nocheck
	import { scaleLinear } from 'd3';
	import * as d3 from 'd3';
	export let intervals;
	export let selectedevent;
	export let attribute_list;
	export let events;
	export let intervalnames;
	export let colorScale;

	let selectedindex;
	let w;
	let eventdata;
	let eventattributes;
	let maxdur;
	let maxfreq;
	let mindur;
	let minfreq;
	let normdata;
	let selected_datapoint = undefined;
	let mouse_x, mouse_y;
	let heightScale;

	$: intervalnames = intervalnames;

	// If component is reloaded, the width of a cell is recomputed based on the amount of attributes from the event type
	function startUpWidth(selectedevent) {
		w = 70 / attribute_list[events.indexOf(selectedevent)].length;
		heightScale = scaleLinear()
			.domain([0, 1])
			.range([0, w - 1]);
	}

	// Add an interval to the selected intervals when a user selects a matrix cell
	function selectintervals(matr, i, j) {
		let intervalname = events[matr] + '/' + attribute_list[matr][i] + '/' + attribute_list[matr][j];
		intervalname = intervalname;
		if (intervalnames.includes(intervalname)) {
			const index = intervalnames.indexOf(intervalname);
			intervalnames.splice(index, 1);
		} else {
			intervalnames.push(intervalname);
		}
		intervalnames = intervalnames;
	}

	// Rounds numbers to two, to list in the tooltip
	function roundToTwo(num) {
		// @ts-ignore
		return +(Math.round(num + 'e+2') + 'e-2');
	}

	// If the data changes, update the normalized date (normdata), and recompute cell width (startupwidth)
	$: {
		eventdata = intervals.filter((d) => d.event === selectedevent);
		maxdur = d3.max(eventdata.map((d) => d.duration));
		mindur = d3.min(eventdata.map((d) => d.duration));
		maxfreq = d3.max(eventdata.map((d) => d.frequency));
		minfreq = d3.min(eventdata.map((d) => d.frequency));
		normdata = eventdata.map((d) => ({
			duration: (d.duration - mindur) / (maxdur - mindur),
			frequency: (d.frequency - minfreq) / (maxfreq - minfreq),
			attr1: d.attr1,
			attr2: d.attr2
		}));
		selectedindex = events.indexOf(selectedevent);
		eventattributes = attribute_list[selectedindex];
		startUpWidth(selectedevent);
	}

	// Extract the cell information when a user hovers over this cell, and compute the mouse position
	function handleHover(event, first, second) {
		selected_datapoint = eventdata
			.filter((d) => d.attr1 == eventattributes[first] && d.attr2 == eventattributes[second])
			.map((e) => ({
				attr1: e.attr1,
				attr2: e.attr2,
				duration: roundToTwo(e.duration),
				frequency: roundToTwo(e.frequency)
			}))[0];
		setMousePosition(event);
	}

	// If a new interval is selected, update the colorscale to include new colors for newly selected intervals
	$: {
		if (intervalnames) {
			colorScale = d3
				.scaleOrdinal()
				.domain(intervalnames)
				.range(d3.schemeCategory10.slice(0, intervalnames.length));
			colorScale = colorScale;
		}
	}

	// Compute the position of the mouse
	const setMousePosition = function (event) {
		mouse_x = event.clientX;
		mouse_y = event.clientY;
		mouse_x = mouse_x;
		mouse_y = mouse_y;
	};
</script>

{#if eventattributes}
	<svg height="100%" width="100%">
		<!-- The legend displays the information that one can see in a cell -->
		<g>
			<rect x="73%" y="0" width="20%" height="20%" fill="white" />
			<text x="75%" y="3%" fill="black" font-size="large" font-weight="bold">legend:</text>
			<rect
				width={12 + '%'}
				height={12 + '%'}
				x="86%"
				y="3%"
				stroke="black"
				style="overflow: visible"
				rx="5"
				fill="white"
				stroke-width="2"
			/>
			<rect x="88%" y="5%" width="3%" height="10%" stroke="black" fill="black" />
			<rect x="93%" y="9%" width="3%" height="6%" stroke="black" fill="black" />
			<text x="89%" y="10%" text-anchor="start" fill="white" font-size="small" font-weight="bold"
				>1</text
			>
			<text x="94%" y="13%" text-anchor="start" fill="white" font-size="small" font-weight="bold"
				>2</text
			>
			<text x="74%" y="8%" text-anchor="start" fill="black" font-size="small" font-weight="bold"
				>1. duration</text
			>
			<text x="74%" y="12%" text-anchor="start" fill="black" font-size="small" font-weight="bold"
				>2. frequency</text
			>
		</g>
		<g>
			<!-- Add text to both axes, that displays the attribute names -->
			{#each eventattributes as attr, i}
				<text
					x={90}
					y={w * i + 22 + '%'}
					dominant-baseline="middle"
					text-anchor="end"
					fill="black"
					font-size="small"
					font-family="arial"
					font-weight="bold">{attr.slice(0, 10)}</text
				>
				<svg x={w * i + 16 + '%'} y="80">
					<text
						dominant-baseline="middle"
						text-anchor="end"
						fill="black"
						font-size="small"
						writing-mode="tb"
						font-family="arial"
						transform="rotate(-60)"
						font-weight="bold">{attr.slice(0, 10)}</text
					>
				</svg>
			{/each}
			{#each Array(eventattributes.length) as _, i}
				{#each Array(eventattributes.length) as _, j}
					<!-- svelte-ignore a11y-mouse-events-have-key-events -->
					<!-- Create mattrix cells -->
					<g
						class="matrixcell"
						on:click={() => selectintervals(selectedindex, j, i)}
						on:mouseover={(event) => handleHover(event, j, i)}
						on:mouseout={() => {
							selected_datapoint = undefined;
						}}
					>
						<!-- The outer rectangle, coloured based on the current selection -->
						<rect
							x={w * i + 14 + '%'}
							y={w * j + 18 + '%'}
							width={w - 1 + '%'}
							height={w - 1 + '%'}
							stroke-width={intervalnames.includes(
								selectedevent +
									'/' +
									attribute_list[selectedindex][j] +
									'/' +
									attribute_list[selectedindex][i]
							)
								? '5'
								: '1'}
							stroke={intervalnames.includes(
								selectedevent +
									'/' +
									attribute_list[selectedindex][j] +
									'/' +
									attribute_list[selectedindex][i]
							)
								? colorScale(
										selectedevent +
											'/' +
											attribute_list[selectedindex][j] +
											'/' +
											attribute_list[selectedindex][i]
								  )
								: normdata.filter(
										(d) => d.attr1 == eventattributes[j] && d.attr2 == eventattributes[i]
								  ).length === 0
								? 'lightgray'
								: 'black'}
							fill="white"
							rx="4"
						/>
						<!-- The first bar, encodes the duration -->
						<rect
							x={w * i + 14 + w / 8 + '%'}
							y={w * j +
								17 +
								w -
								heightScale(
									normdata
										.filter((d) => d.attr1 == eventattributes[j] && d.attr2 == eventattributes[i])
										.map((e) => e.duration)
								) +
								'%'}
							width={w / 3 + '%'}
							height={heightScale(
								normdata
									.filter((d) => d.attr1 == eventattributes[j] && d.attr2 == eventattributes[i])
									.map((e) => e.duration)
							) + '%'}
							fill={intervalnames.includes(
								selectedevent +
									'/' +
									attribute_list[selectedindex][j] +
									'/' +
									attribute_list[selectedindex][i]
							)
								? colorScale(
										selectedevent +
											'/' +
											attribute_list[selectedindex][j] +
											'/' +
											attribute_list[selectedindex][i]
								  )
								: 'black'}
						/>
						<!-- The second bar, encodes the frequency -->
						<rect
							x={w * i + 14 + w / 2 + '%'}
							y={w * j +
								17 +
								w -
								heightScale(
									normdata
										.filter((d) => d.attr1 == eventattributes[j] && d.attr2 == eventattributes[i])
										.map((e) => e.frequency)
								) +
								'%'}
							width={w / 3 + '%'}
							height={heightScale(
								normdata
									.filter((d) => d.attr1 == eventattributes[j] && d.attr2 == eventattributes[i])
									.map((e) => e.frequency)
							) + '%'}
							fill={intervalnames.includes(
								selectedevent +
									'/' +
									attribute_list[selectedindex][j] +
									'/' +
									attribute_list[selectedindex][i]
							)
								? colorScale(
										selectedevent +
											'/' +
											attribute_list[selectedindex][j] +
											'/' +
											attribute_list[selectedindex][i]
								  )
								: 'black'}
						/>
					</g>
				{/each}
			{/each}
		</g></svg
	>
	<!-- Add tooltip to each cell -->
	{#if selected_datapoint != undefined}
		<div id="tooltip" style="left: {mouse_x}px; top: {mouse_y}px;">
			<p class="font-bold text-black">
				Interval: {selected_datapoint.attr1}/{selected_datapoint.attr2}
			</p>
			<p class="text-black">Average summed duration: {selected_datapoint.duration} minutes</p>
			<p class="text-black">Average frequency: {selected_datapoint.frequency}</p>
		</div>
	{/if}
{/if}

<style>
	.matrixcell:hover rect {
		filter: opacity(0.4);
	}

	svg svg {
		overflow: visible;
	}

	#tooltip {
		background-color: white;
		position: fixed;
		border: 2px solid lightgray;
		border-radius: 15px;
	}
</style>
