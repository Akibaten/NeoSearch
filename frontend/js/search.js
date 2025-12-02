async function getSearchData(query,page){ 
  try{
    const response = await fetch(`https://neosearch.onrender.com/search?q=${query}`);
    const data = await response.json();

    let pageNumber = page;
    search_results = data['results'].slice(15* (pageNumber-1), 15*pageNumber);
    return search_results;
  }
  catch(error){
    console.log(error);
    return    
  }
}

function renderResults(searchResults){
  //elements of results
  resultElements = "";

  for(result of searchResults){
    resultElements += `<p><a href=${result}>${result}</a></p>`    
  }
  document.getElementById("results").innerHTML = resultElements;
}
