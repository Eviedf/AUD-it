<script>
	import BoopAction from '../boop/BoopAction.svelte';
	import HelpButton from '../boop/HelpButton.svelte';
	import SequencePopup from './SequencePopup.svelte';
	import IntervalDuration from './IntervalDuration.svelte';
	import RadialChart from './radialChart.svelte';
	import { Circle3 } from 'svelte-loading-spinners';
	export let selecteddurs;
	export let selectedhours;
	export let colorScale;
	export let highlight;
	export let timedata;
	export let intervalnames;
	export let selectedsets;
	export let reload;

	let dur_data;
	let selected_interval;
	let selecteddata;
	let reloadPlot = 0;
	let updateplot = 0;
	let radial_data;
	let detailed_data;
	let color;
	let loading = false;
	let neww;

	// If component is reloaded, reset parameters
	function startUpDur(reload) {
		dur_data = '';
		selected_interval = '';
		selecteddata = '';
		updateplot = 0;
		reloadPlot = 0;
		radial_data = '';
		color = '';
		loading = false;
	}
	// Reload plot on change in param reload
	$: startUpDur(reload);

	let today = new Date();
	today = today.setHours(0, 0, 0, 0);

	// Group json object by a key
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
		return Array.from(map);
	}

	// Convert the data to create the duration and radial view (dur_data) by changing the date of the start and end time to today
	async function loadDuration() {
		dur_data = '';
		highlight = '';
		selectedhours = undefined;
		loading = true;
		let interval_names = JSON.stringify(intervalnames.map((d) => d.replaceAll('/', '-')));
		let _duration = await fetch(
			'http://127.0.0.1:5000/get_intervals/' + selectedsets + '/' + interval_names
		);
		dur_data = await _duration.json();
		timedata = structuredClone(dur_data);
		console.log('timedata', timedata);
		dur_data.forEach(function (d) {
			var splitdata = d.start_time.split(/ /);
			var parts = splitdata[1].split(/:/);
			var timePeriodMillis =
				parseInt(parts[0], 10) * 60 * 60 * 1000 +
				parseInt(parts[1], 10) * 60 * 1000 +
				parseInt(parts[2], 10) * 1000;

			d.start_time = new Date();
			d.start_time.setTime(today + timePeriodMillis);
			var splitdata = d.end_time.split(/ /);
			var parts = splitdata[1].split(/:/);
			var timePeriodMillis =
				parseInt(parts[0], 10) * 60 * 60 * 1000 +
				parseInt(parts[1], 10) * 60 * 1000 +
				parseInt(parts[2], 10) * 1000;

			d.end_time = new Date();
			d.end_time.setTime(today + timePeriodMillis);
		});
		dur_data = groupBy(dur_data, (e) => e.value);
		selecteddurs = {};
		selected_interval = dur_data[0][0];
		loading = false;
	}

	// Compute color based on the selected interval
	$: if (selected_interval) {
		color = colorScale(selected_interval);
	}

	// compute data for the duration view (selecteddata)
	$: if (selected_interval && !!dur_data) {
		selecteddata = dur_data.filter((d) => d[0] === selected_interval).map((e) => e[1])[0];
		selecteddata = selecteddata;
		reloadPlot += 1;
	}

	// compute data for the radial view (radial_data) and detailed view (detailed_data)
	$: if (
		dur_data &&
		selected_interval &&
		Object.keys(selecteddurs).includes(selected_interval.replaceAll('/', '-'))
	) {
		let durations = selecteddurs[selected_interval.replaceAll('/', '-')];
		radial_data = dur_data
			.filter((d) => d[0] === selected_interval)
			.map((e) => e[1])[0]
			.filter((f) => durations[0] <= f.duration && f.duration <= durations[1]);
		detailed_data = new Array();

		intervalnames.forEach(
			(key) => (
				Object.keys(selecteddurs).includes(key.replaceAll('/', '-'))
					? (neww = timedata.filter(
							(e) =>
								e.value === key &&
								selecteddurs[key.replaceAll('/', '-')][0] <= e.duration &&
								e.duration <= selecteddurs[key.replaceAll('/', '-')][1]
					  ))
					: (neww = timedata.filter((e) => e.value === key)),
				detailed_data.push(neww)
			)
		);
		const flatten = (obj) => Object.values(obj).flat();

		detailed_data = flatten(detailed_data);
		radial_data = radial_data;
		updateplot += 1;
	} else if (dur_data) {
		radial_data = dur_data.filter((d) => d[0] === selected_interval).map((e) => e[1])[0];
		detailed_data = timedata;
		radial_data = radial_data;
		updateplot += 1;
	}

	// update variables on change
	$: selected_interval = selected_interval;
	$: reloadPlot = reloadPlot;

	// remove duration from the selection (selecteddurs)
	function removeDuration(key, val) {
		delete selecteddurs[key];
		console.log(selecteddurs);
		selecteddurs = selecteddurs;
	}
</script>

{#if selecteddata}
	{#if loading}
		<div class="h-1/3 rounded border-2 bg-slate-100 border-slate-800" />
	{:else}
		<div class="h-1/3 w-full rounded border-2 border-slate-800 overflow-visible">
			<div class="flex flex-row-reverse">
				<!-- Include tooltip with information about duration view -->
				<div
					class="tooltip tooltip-bottom z-10"
					data-tip="The duration view displays the duration distribution for a selected interval of interest. You can zoom in and select a range of interest to filter out other intervals for further exploration."
				>
					<BoopAction boopParams={{ scale: 1.2, timing: 200 }}>
						<HelpButton />
					</BoopAction>
				</div>
				<!-- Dropdown to select one interval from the selected intervals in the matrix -->
				<select bind:value={selected_interval}>
					{#each dur_data as interval}
						<option value={interval[0]}>
							{interval[0]}
						</option>
					{/each}
				</select>
				<!-- Button to compute the durationa and radial view -->
				<button class="mt-3 btn ghost-btn" on:click={loadDuration}>Show interval durations</button>
			</div>
			<!-- Duration view -->
			<IntervalDuration bind:dur_data={selecteddata} bind:selecteddurs bind:reloadPlot bind:color />
			<!-- Display selected durations (if any) -->
			{#if selecteddurs}
				{#each Object.entries(selecteddurs) as [key, value]}
					{#if value.length > 0}
						<span
							class="badge badge-lg mr-1 mt-1"
							style="background-color: {colorScale(key.replaceAll('-', '/'))}"
						>
							<span
								>{key}: {Math.round(value[0])}, {Math.round(value[1])}
								<button type="button" on:click={removeDuration(key, value)}>
									<span aria-hidden="true">&times;</span>
								</button></span
							>
						</span>
					{/if}
				{/each}
			{/if}
		</div>
	{/if}
	<!-- If the duration data is not yet computed, show empty component. Disable button if there are no intervals selected in the matrix view -->
{:else if intervalnames.length > 0}
	<div class="h-1/3 rounded border-2 bg-slate-100 border-slate-800">
		<button class="mt-3 btn ghost-btn" on:click={loadDuration}>Show interval durations</button>
		<div class="flex justify-center items-center h-80">
			<p
				class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
				data-tip="The summary view displays the average frequency and duration of selected intervals based on the selected duration- and time-range from the duration and the radial view."
			>
				Duration view
			</p>
		</div>
	</div>
{:else}
	<div class="h-1/3 rounded border-2 bg-slate-100 border-slate-800">
		<button class="mt-3 btn ghost-btn btn-disabled">Show interval durations</button>
		<div class="flex justify-center items-center h-80">
			<p
				class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
				data-tip="The duration view displays the duration distribution for a selected interval of interest. You can zoom in and select a range of interest to filter out other intervals for further exploration."
			>
				Duration view
			</p>
		</div>
	</div>
{/if}

{#if radial_data}
	{#if loading}
		<!-- Indicata that the duration and radial view are loading -->
		<div class="h-2/3 rounded border-2 bg-slate-100 border-slate-800">
			<div class="flex justify-center items-center h-60">
				<Circle3 size="150" />
				<p>Loading... this might take a few minutes</p>
			</div>
		</div>
	{:else}
		<div class="h-2/3 w-full rounded border-2 border-slate-800">
			<div class="flex flex-row-reverse">
				<!-- Tooltip that explains the radial view -->
				<div
					class="tooltip tooltip-left overflow-visible"
					data-tip="The radial view displays clustered sequences for a selected interval of interest on a radial 24-hour timeline. Black circles around a group of sequences indicate a cluster. Coloured bars indicate the times where this interval occurs. If a pattern is selected from the pattern view, the intervals that follow this pattern will be highlighted. Moreover, one can select specific durations from the duration view to filter the intervals in this radial view."
				>
					<BoopAction boopParams={{ scale: 1.2, timing: 200 }}>
						<HelpButton />
					</BoopAction>
				</div>
				<div class="w-1/3" />
				<!-- Detailed view component -->
				<SequencePopup
					bind:highlight
					bind:colorScale
					bind:timedata={detailed_data}
					bind:selectedhours
				/>
			</div>
			<div class="overflow-hidden">
				<!-- Radial view component -->
				<RadialChart
					timedata={radial_data}
					bind:updateplot
					bind:selectedhours
					bind:color
					bind:highlight
				/>
			</div>
		</div>
	{/if}
{:else}
	<!-- Show empty component if there is no duration data loaded -->
	<div class="h-2/3 rounded border-2 bg-slate-100 border-slate-800">
		{#if loading}
			<!-- Indicata that the duration and radial view are loading -->
			<div class="flex justify-center items-center h-60">
				<Circle3 size="150" />
			</div>
			<p>Loading... this might take a few minutes</p>
		{:else}
			<div class="flex justify-center items-center h-80">
				<p
					class="text-8xl text-center text-slate-300 hover:text-slate-400 tooltip"
					data-tip="The radial view displays clustered sequences for a selected interval of interest on a radial 24-hour timeline. If a pattern is selected from the pattern view, the intervals that follow this pattern will be highlighted. Moreover, one can select specific durations from the duration view to filter the intervals in this radial view."
				>
					Radial view
				</p>
			</div>
		{/if}
	</div>
{/if}
