const dataset_info = {{ periodic_table_data_json }}

// all species associated with a dataset
// let all_species = [];
// Object.entries(dataset_info).forEach(([colabfit_id, h]) => {
//   all_species = all_species.concat( h['s'] );
// });
// console.log([...new Set(all_species)].sort());
const all_species = ["Ag", "Al", "Ar", "As", "Au", "B", "Ba", "Be", "Bi", "Br", "C", "Ca", "Cd", "Cl", "Co", "Cr", "Cs", "Cu", "F", "Fe", "Ga", "Ge", "H", "He", "Hf", "Hg", "I", "In", "Ir", "K", "Kr", "Li", "Mg", "Mn", "Mo", "N", "Na", "Nb", "Ne", "Ni", "O", "Os", "P", "Pb", "Pd", "Pt", "Rb", "Re", "Rh", "Ru", "S", "Sb", "Sc", "Se", "Si", "Sn", "Sr", "Ta", "Tc", "Te", "Ti", "Tl", "V", "W", "Xe", "Y", "Zn", "Zr"];


function periodic_table_button(species=null) {
  let s = '';

  Array.from( document.getElementsByClassName("pt-active") ).forEach((el) => {
    el.classList.remove("pt-active");
  });
  e_pt_table = document.getElementById( `pt-${species}` );
  e_pt_table.classList.add("pt-active");

  let e_datasets_search_header = document.getElementById('datasets-search-header');
  //let e_datasets_search_button_view_all = document.getElementById('datasets-search-button-view-all');
  if( species ) {
    e_datasets_search_header.innerHTML = `Datasets - Species ${species}`;
    //e_datasets_search_button_view_all.style.display = 'block';
  } else {
    e_datasets_search_header.innerHTML = `Datasets`;
    //e_datasets_search_button_view_all.style.display = 'none';
  }

  if( !species || all_species.includes(species) ) {
    s += '<table class="table table-sm table-bordered">';
    s += `<tr><th style="min-width: 6em;">Species</th><th>Dataset ID</th></tr>`;

/*
    Object.entries(dataset_info).forEach(([colabfit_id, h]) => {
      if( !species || h['s'].includes(species) ) {
        s += `<tr><td>${h['s'].join(', ')}</td>`;
        s += `<td><a target=_blank href="https://materials.colabfit.org/id/${colabfit_id}">${h['e']}</a></td></tr>`;
      }
    });
    */
    Object.entries(dataset_info).forEach(([extended_colabfit_id, dataset_ary]) => {
      if( !species || dataset_ary.includes(species) ) {
        const short_colabfit_id = extended_colabfit_id.split('__').slice(-1);
        s += `<tr><td>${dataset_ary.join(', ')}</td>`;
        s += `<td><a target=_blank href="https://materials.colabfit.org/id/${short_colabfit_id}">${extended_colabfit_id}</a></td></tr>`;
      }
    });

    s += '</table>';
  } else {
    s += `No Dataset available with element ${species}`;
  }
  e = document.getElementById('datasets');
  e.innerHTML = s;
}


