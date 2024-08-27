let global_current_page = 1;
let global_total_number_of_pages = null;

function set_total_number_of_pages(page_size=5000) {
  page_size = parseInt(page_size);
  return Math.ceil( global_cache_data.length / page_size );
}


function next_page() {
  if( global_current_page >= global_total_number_of_pages ) {
    paginate_table( 1 );
  } else {
    paginate_table( global_current_page + 1 );
  }
}


function previous_page() {
  if( global_current_page <= 1 ) {
    paginate_table( global_total_number_of_pages );
  } else {
    paginate_table( global_current_page - 1 );
  }
}


function paginate_table(page_num, page_size=5000) {
  page_num = parseInt(page_num);
  global_current_page = page_num;
  page_size = parseInt(page_size);
  slice_begin = page_size * (page_num - 1);
  slice_end = page_size + slice_begin;

  page_selector_select(page_num);

  let s = "";
  s += `<tr><th>ColabFit ID</th><th>Name</th><th>Description</th></tr>`;

  global_cache_data.slice(slice_begin, slice_end).forEach((ary) => {
    let colabfit_id = ary[0];
    let description = ary[1]['d'];
    let name = ary[1]['n'];
    //let count = ary[1]['i'];
    //s += `<tr><td>${count}</td><td class="font-monospace"><a target=_blank href="/id/${colabfit_id}">${colabfit_id}</a></td><td>${description}</td></tr>`;
    if( name ) {
      // wrap 'name' cell with div below for Firefox, see https://stackoverflow.com/a/9789989
      s += `<tr><td class="font-monospace"><a target=_blank href="/id/${colabfit_id}">${colabfit_id}</a></td><td style="max-width: 220px; overflow: auto;"><div style="overflow: auto;">${name}</div></td><td class="cell-description" style="max-width: 540px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${description}</td></tr>`;
    } else {
      s += `<tr><td class="font-monospace"><a target=_blank href="/id/${colabfit_id}">${colabfit_id}</a></td><td>${description}</td></tr>`;
    }
  });
  e = document.getElementById("paginated-items");
  e.innerHTML = s;
}


function page_selector_populate() {
  e = document.getElementById("page-select");
  s = "";
  for (let i=1; i<=global_total_number_of_pages; i++) {
    s += `<option value="${i}">Page ${i} of ${global_total_number_of_pages}</option>`;
  }
  e.innerHTML = s;

  if( global_total_number_of_pages <= 1) {
    e = document.getElementById('page-navigation-section');
    e.style.display = 'none';
  }
}


function page_selector_select( page_num ) {
  page_num = parseInt(page_num);
  e = document.getElementById("page-select");
  e.value = page_num;
}

global_total_number_of_pages = set_total_number_of_pages();
page_selector_populate();
paginate_table(global_current_page);
