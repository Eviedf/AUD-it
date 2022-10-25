<script>
	// code based on https://svend3r.dev/charts/radialStacked
	import { fade } from 'svelte/transition';
	import { arc, max, scaleRadial } from 'd3';
	export let timedata;
	export let updateplot;
	import * as d3 from 'd3';
	import circularbrush from './circularBrush.js';
	import { select } from 'd3';
	export let selectedhours;
	export let color;
	export let highlight;

	let width;
	let innerRadius;
	let chartScale;
	let varFontSize;
	let height;
	let outerRadius;
	let yScale;

	let maxorder = max(timedata.map((d) => d.order)) / 100;

	// On reload of radial view, reset parameters
	function startUpRadius(updateplot) {
		console.log('radial plot updates');
		width = 900; // width of inner radius inverted, in pixels
		innerRadius = 110; // radius of inner circle, in pixels
		chartScale = 0.38; // scale factor from the center
		varFontSize = 10; // font size of chart text, in pixels
		height = width;
		outerRadius = width * chartScale;
	}

	// group js object (list) by keygetter
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

	// group timedata by label (clusterlabel)
	$: groupedBy = Array.from(groupBy(timedata, (e) => e.label));

	$: startUpRadius(updateplot);

	// extract sequence order within clusters
	$: cluster_order = groupedBy.map((d) => ({
		cluster: d[0],
		first: d3.min(d[1].map((e) => e.order)),
		last: d3.max(d[1].map((e) => e.order))
	}));

	let today = new Date();
	today = today.setHours(0, 0, 0, 0);
	// extent of x-axis (circular)
	let xExtent = [today, new Date().setHours(23, 59)];

	// set circular xScale
	$: xScale = d3
		.scaleTime()
		.domain(xExtent)
		.nice(d3.timeDay)
		.range([0, 2 * Math.PI]);

	// set yscaele based on radius
	$: yScale = scaleRadial()
		.domain([0, d3.max(timedata, (d) => d.order) + 1])
		.range([innerRadius, outerRadius]);

	// Create an arc (circular lines)
	$: d3arc = arc()
		.innerRadius((d) => yScale(d.order))
		.outerRadius((d) => yScale(d.order + 1))
		.startAngle((d) => xScale(d.start_time))
		.endAngle((d) => xScale(d.end_time) + 0.01)
		.padAngle(0.01)
		.padRadius(innerRadius);

	// highligted arcs are a bit bigger
	$: highlightarc = arc()
		.innerRadius((d) => yScale(d.order))
		.outerRadius((d) => yScale(d.order + maxorder + 1))
		.startAngle((d) => xScale(d.start_time) - 0.05)
		.endAngle((d) => xScale(d.end_time) + 0.05)
		.padAngle(0.01)
		.padRadius(innerRadius);

	// cruate the full circle (arc)
	$: fullarc = arc()
		.innerRadius((d) => yScale(d.first))
		.outerRadius((d) => yScale(d.last + 1))
		.startAngle(0)
		.endAngle(2 * Math.PI)
		.padAngle(0.01)
		.padRadius(innerRadius);

	let brushElement;
	// create the brush that can be used to select a timeframe
	$: hoursbrush = circularbrush(d3)
		.range([0, 24])
		.innerRadius(innerRadius)
		.outerRadius(outerRadius)
		.handleSize(0.1)
		.addCallback(brush);

	$: if (brushElement) {
		select(brushElement).call(hoursbrush);
	}
	// if brush is changed, update the selected hours
	function brush(_, extent) {
		selectedhours = extent;
	}

	$: yScale = yScale;
</script>

{#if width}
	<svg
		class="radial-chart"
		viewBox="{-width / 2} {-height / 2} {width} {height}"
		font-size="{varFontSize}px"
	>
		<g class="chart-render">
			{#each timedata as d}
				<!-- create all the circles -->
				{#if highlight}
					<!-- If a pattern is selected, create highlighted arcs that adhere to the pattern, other arcs will be gray -->
					{#if !highlight.includes(d.eid)}
						<g fill="lightgray">
							<path d={d3arc(d)} />
						</g>
					{:else if highlight.includes(d.eid)}
						<g fill={color}>
							<path d={highlightarc(d)} />
						</g>
					{/if}
				{:else}
					<!-- If no pattern is selected, colour all the arcs -->
					<g fill={color}>
						<path d={d3arc(d)} />
					</g>
				{/if}
			{/each}
			{#each cluster_order as c}
				<!-- Create cluster circles -->
				<g fill="none">
					<circle
						stroke="black"
						stroke-opacity="0.5"
						stroke-width="5"
						r={yScale(c.last + 1)}
						transition:fade
					/>
				</g>
			{/each}
			<!-- Make clusters responsive to hover events (class cluster_arc) -->
			{#each cluster_order as c}
				<!-- svelte-ignore a11y-mouse-events-have-key-events -->
				<g fill="none">
					<path class="cluster_arc" d={fullarc(c)} />
				</g>
			{/each}
		</g>
		<!-- Create the brush, to select timeframes -->
		<g
			class="brush"
			viewBox="{-width / 2} {-height / 2} {width} {height}"
			bind:this={brushElement}
		/>
		<!-- Add the x-scale ticks and labels -->
		<g class="x-axis" text-anchor="middle">
			{#each xScale.ticks() as tick, i}
				<g transform="rotate({(xScale(tick) * 180) / Math.PI - 90}) translate({innerRadius},0)">
					<line x2="-5" stroke="black" />
					<text
						font-size="large"
						transform={(xScale(tick) + Math.PI / 2) % (2 * Math.PI) < Math.PI
							? 'rotate(90) translate(0,30)'
							: 'rotate(-90) translate(0,-23)'}>{tick.getHours() + ':00'}</text
					>
				</g>
			{/each}
		</g>
	</svg>
{/if}

<style global>
	.extent {
		fill-opacity: 0.1;
		fill: rgba(238, 203, 4, 0.801);
		cursor: move;
	}

	.resize {
		fill-opacity: 0.5;
		cursor: move;
		stroke: black;
		stroke-width: 1px;
	}

	.cluster_arc {
		fill: none;
		stroke: black;
		pointer-events: all;
	}

	.cluster_arc:hover {
		fill: gray;
		stroke: black;
		fill-opacity: 0.3;
	}
</style>
