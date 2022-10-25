<script>
	import TimeLine from '../TimeLine.svelte';
	import { Circle3 } from 'svelte-loading-spinners';
	export let message;
	export let timedata;
	export let highlight;
	export let colorScale;
	export let selectedhours;

	let patterndata;

	// Group list by keygetter
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

	$: groupeddata = Array.from(groupBy(timedata, (e) => e.sid));

	// filter patterndata if a pattern is selected
	$: if (highlight) {
		patterndata = groupeddata
			.filter((d) => d[1].map((e) => e.eid).some((f) => highlight.includes(f)))
			.map((g) => g[1])
			.flat();
	} else {
		patterndata = groupeddata.map((g) => g[1]).flat();
	}
	// Convert selectedhours to positive numbers if they are somehow negative
	$: if (selectedhours) {
		if (selectedhours[0] < 0) {
			selectedhours[0] = 24 + selectedhours[0];
		}
		if (selectedhours[1] < 0) {
			selectedhours[1] = 24 + selectedhours[1];
		}
	}
</script>

<h1>{message}</h1>

{#if patterndata}
	<!-- Display timeline in the popup (detailed view) -->
	<TimeLine {patterndata} {colorScale} {highlight} {selectedhours} />
{:else}
	<!-- Indicate that the data is loading -->
	<div class="flex justify-center items-center h-60">
		<Circle3 size="150" />
	</div>
{/if}

<style>
	h1 {
		font-size: 2rem;
		text-align: center;
	}
</style>
