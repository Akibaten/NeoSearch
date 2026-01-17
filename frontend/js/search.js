let fontList = [
  "Times-New-Roman",
  "Georgia",
  "Segoe-UI-Semilight",
  "Arial-Narrow",
  "rainyhearts",
  "PixelifySans",
  "courier",
  "Fredoka",
  "remington",
  "nunito",
  "Frutiger",
  "NEC_AP3",
  "verdana",
  "alice",
  "space-grotesk",
  "short-stack",
  "kosugi-maru"
]

class SearchResult{
  constructor(site_url, profile_url, site_title){
    this.font = fontList[Math.floor(Math.random()*fontList.length)];
    this.site_title_p = `<p class = "site-title" style="font-family: '${this.font}'
"><a target="_blank" href="${site_url}">${site_title}</a></p>`;
    this.site_url_p = `<p class = "site-url" style="font-family: '${this.font}'
"><a target="_blank" href="${site_url}">${site_url}</a></p>`;
    this.profile_url_p = `<p class = "profile-url" style="font-family: '${this.font}'
"><a target="_blank" href="${profile_url}">${profile_url}</a></p>`;

    this.div = `<div class="search-result">
                ${this.site_title_p}
                ${this.site_url_p}
                ${this.profile_url_p}
                </div>`;
  }
}

async function getSearchData(query,page){ 
  try{
    const response = await fetch(`https://service.neosearch.site/search?q=${query}`);
    const data = await response.json();

    let sitesPerPage = 10;

    page = parseInt(page);

    // puts the searched item in the search bar on page load
    document.getElementById('search-bar-input').value = query;
    
    //makes pages links for navigation at the bottom
    pageLinks = ""

    if(page < 5){
      for(site=1; site<Math.ceil(data['site_urls'].length/sitesPerPage) && site <= 10; ++site){
        if(site == page){
          pageLinks += `<a style = "color: blue" href = "/search?q=${query}&page=${site}">${site}</a>`;
        }else{
          pageLinks += `<a href = "/search?q=${query}&page=${site}">${site}</a>`;
        }
      }
      if(data['site_urls'][((page+5)*sitesPerPage)+5]){
        pageLinks += `<a href= "/search?q=${query}&page=${page+10}">...</a>`
      }
    }else{
      pageLinks += `<a href = "/search?q=${query}&page=1">1</a>`
      pageLinks += `<a href = "/search?q=${query}&page=1">...</a>`
      for(site=page-2; site<Math.ceil(data['site_urls'].length/sitesPerPage) && site <= page+8; ++site){
        if(site == page){
          pageLinks += `<a style = "color: hotpink" href = "/search?q=${query}&page=${site}">${site}</a>`;
        }else{
          pageLinks += `<a href = "/search?q=${query}&page=${site}">${site}</a>`;
        }
      }
      if(data['site_urls'][((page+5)*sitesPerPage)+5]){
        pageLinks += `<a href= "/search?q=${query}&page=${page+9}">...</a>`
      }
    }   
    document.getElementById("page-navigation").innerHTML = pageLinks;

    document.getElementById("query-duration").innerHTML = `${data['site_urls'].length} sites found in ${data['query_duration']} seconds`
    
    // NOTE 2025-12-06 you should rewrite this so that it make a new class instance for each
    // result and it all gets passed into the next function as just one array MUCH more concise
    let search_results = [];
    for(i = 0; i<sitesPerPage; i++){
      const index = (page-1)*sitesPerPage+i;
      if(data['site_urls'][index]){
        search_results.push(new SearchResult(data['site_urls'][index], data['profile_urls'][index], data['site_title'][index]));    
      }
    }
    return search_results;
  }
  catch(error){
    console.log(error);
  }
}

function renderResults(searchResults){
  //makes result section visible
  document.getElementById('results-page').style = "visibility: visible";

  resultElements = "";
  if(searchResults){
    for(site of searchResults){
      // for some reason this is showing a lot of dollar signs in the output url... I think the problem is this line
      document.getElementById("results").innerHTML += `${site.div}`;
    }
  }else{
    document.getElementById("results").innerHTML +=
    "<div class = 'no-results'><p>no results >W< <br> Maybe try a different search?</p></div> "
  }
}
