<script>
	import * as d3 from 'd3';
	export let patterndata;
	export let highlight;
	export let colorScale;
	export let selectedhours;

	// Initiate parameters
	let users = [...new Set(patterndata.map((d) => d.participant_id))];
	let dates = [...new Set(patterndata.map((d) => d.timebin))];
	let intervals = [...new Set(patterndata.map((d) => d.value))];
	let selected_user = users[0];
	let selected_date = dates[0];
	let width = 0.7 * screen.width;
	let height = 500;
	const lbuffer = 250;
	const rbuffer = 50;
	const ybuffer = 50;
	let boundaries;

	const parseDate = d3.timeParse('%Y/%m/%d');
	const parseTime = d3.timeParse('%Y/%m/%d %H:%M:%S');

	$: userdata = patterndata.filter((d) => d.participant_id === selected_user);
	// Extract the dates based on the selected user
	$: dates = [...new Set(userdata.map((d) => d.timebin))];

	// Extract timeline data by filtering the data on the selected user and date
	$: timelinedata = patterndata.filter(
		(d) => d.participant_id === selected_user && d.timebin === selected_date
	);

	// Scalefactor to compute the width of interval rectangles in the timeline
	$: scaleFactor =
		(1 / (parseDate(selected_date).setHours(23, 59, 59) - parseDate(selected_date).getTime())) *
		(width - lbuffer - rbuffer);

	// Set extent to the time range of the selected date
	$: xExtent = [parseDate(selected_date), new Date(parseDate(selected_date).setHours(23, 59, 59))];

	// time scale (x scale)
	$: xScale = d3
		.scaleTime()
		.domain(xExtent)
		.nice(d3.timeDay)
		.range([lbuffer, width - rbuffer]);

	// categorical interval scale (y scale)
	$: yScale = d3
		.scalePoint()
		.domain(intervals)
		.range([0, height - 30 - ((height - ybuffer - 30) / intervals.length + 6)]);

	// if a time is selected from the radial view, set the boundaries
	$: if (selectedhours) {
		boundaries = [
			new Date(new Date(selected_date).setHours(selectedhours[0])),
			new Date(new Date(selected_date).setHours(selectedhours[1]))
		];
	}
</script>

<!-- dropdown to select user, if a group is selected -->
{#if users.length > 1}
	<div class="form-control flex-row">
		<div class="ml-6 flex-col">
			<p class="font-bold">Select user:</p>
			<select bind:value={selected_user}>
				{#each users as user}
					<option value={user}>
						{user}
					</option>
				{/each}
			</select>
		</div>
	</div>
{/if}
<!-- dropdown to select date -->
<div class="form-control flex-row">
	<div class="ml-6 flex-col">
		<p class="font-bold">Select date:</p>
		<select bind:value={selected_date}>
			{#each dates as date}
				<option value={date}>
					{date}
				</option>
			{/each}
		</select>
	</div>
</div>

<div>
	<svg {height} {width}>
		<!-- Indicate time boundaries with dotted line and gray area -->
		{#if boundaries}
			<line
				x1={xScale(boundaries[0])}
				x2={xScale(boundaries[0])}
				y1={height - 30}
				y2="0"
				stroke="black"
				stroke-dasharray="4"
				stroke-width="3"
			/>
			<line
				x1={xScale(boundaries[1])}
				x2={xScale(boundaries[1])}
				y1={height - 30}
				y2="0"
				stroke="black"
				stroke-dasharray="4"
				stroke-width="3"
			/>
			{#if selectedhours[0] > selectedhours[1]}
				<rect
					x={xScale(boundaries[0])}
					y={height}
					width={width - xScale(boundaries[1])}
					height={height - 10}
					fill="lightgrey"
					fill-opacity="50%"
				/>
				<rect
					x={lbuffer}
					y={height}
					width={xScale(boundaries[1]) - lbuffer}
					height={height - ybuffer}
					fill="lightgrey"
					fill-opacity="50%"
				/>
			{:else}
				<rect
					x={xScale(boundaries[0])}
					y="0"
					width={xScale(boundaries[1]) - xScale(boundaries[0])}
					height={height - 30}
					fill="lightgrey"
					fill-opacity="50%"
				/>
			{/if}
		{/if}

		{#each timelinedata as item}
			<!-- create rectangles for the intervals in the data, highlight them if they occur in the selected pattern -->
			<rect
				x={xScale(parseTime(item.start_time))}
				y={yScale(item.value)}
				width={item.duration < 5
					? (parseTime(item.end_time).getTime() - parseTime(item.start_time).getTime()) *
							scaleFactor +
					  2
					: (parseTime(item.end_time).getTime() - parseTime(item.start_time).getTime()) *
					  scaleFactor}
				height={(height - ybuffer - 30) / intervals.length + 6}
				fill={colorScale(item.value)}
				fill-opacity={highlight.includes(item.eid) ? '80%' : '40%'}
				stroke={highlight.includes(item.eid) ? 'black' : 'none'}
				stroke-width={highlight.includes(item.eid) ? 2 : 0}
			/>
		{/each}
		<!-- Set x-axis line, ticks and labels -->
		<line x1={lbuffer - 20} x2={width - 70} y1={height - 30} y2={height - 30} stroke="black" />
		{#each xScale.ticks(12) as tick}
			<g transform={`translate(${xScale(tick)} ${height})`}>
				<line y1="-30" y2="-25" stroke="black" />
				<text y="-10" text-anchor="middle" font-size="smaller">{tick.getHours() + ':00'}</text>
			</g>
		{/each}
		<!-- Set y axis labels -->
		{#each intervals as interval}
			<g transform={`translate(${0} ${yScale(interval)})`}>
				<text
					y={height / 2 / intervals.length}
					text-anchor="left"
					font-size="medium"
					font-weight="bold">{interval}</text
				>
			</g>
		{/each}
	</svg>
</div>
