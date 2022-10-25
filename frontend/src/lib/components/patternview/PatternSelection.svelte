<script>
	export let intervalnames;
	export let pattern_data;
	export let updatePatterns;
	export let selecteddurs;
	export let selectedhours;
	export let selectedsets;
	export let pattern_intervals;
	export let pattern_relations;
	export let patternloading;

	let selectedpatterns = 'all';

	// Mine patterns from selected sequences
	async function minePatterns() {
		pattern_data = '';
		patternloading = true;
		let interval_names = JSON.stringify(intervalnames.map((d) => d.replaceAll('/', '-')));
		let selected_patterns = JSON.stringify(selectedpatterns.replaceAll('/', '-'));
		let selected_durs = JSON.stringify(selecteddurs);
		let _total_data = await fetch(
			'http://127.0.0.1:5000/get_pattern_data/' +
				selectedsets +
				'/' +
				interval_names +
				'/' +
				selected_durs +
				'/' +
				selectedhours +
				'/' +
				selected_patterns
		);
		pattern_data = await _total_data.json();
		updatePatterns += 1;
		pattern_intervals = '';
		pattern_relations = '';
	}
</script>

<!-- dropdown to indicate from which sequences patterns should be mined -->
<div class="form-control flex-row">
	<button class="mt-6 btn ghost-btn" on:click={minePatterns}>Mine Patterns</button>
	<div class="ml-6 flex-col">
		<p class="font-bold">In sequences with:</p>
		<select bind:value={selectedpatterns}>
			<option value={'all'}> any selected interval </option>
			{#each intervalnames as val}
				<option value={val}>
					{val}
				</option>
			{/each}
		</select>
	</div>
</div>
