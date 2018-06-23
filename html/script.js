

$(document).ready(function() {
  
  var amountScrolled = 200;
  var amountScrolledNav = 25;
  var windowHeight = window.innerHeight

  var cardHeight = $(".card").height();
  var numberOfCards = $(".card").length

  $(window).scroll(function() {
    if ( $(window).scrollTop() > amountScrolled ) {
      $('button.back-to-top').addClass('show');
    } else {
      $('button.back-to-top').removeClass('show');
    }
  });

  $('button.back-to-top').click(function() {
    $('html, body').animate({
      scrollTop: 0
    }, 800);
    return false;
  });

  $(document).keypress(function(event) {
    var keycode = event.keyCode || event.which;
    if(keycode == '37') {
        console.log(cardHeight);    
    }
});

  $(window).resize(function() {
    windowHeight = window.innerHeight
    cardHeight = $(".card").height(); 
  });

});


/* 

divide page into sections by taking window(?) % 900;
getCurrentWindowLocation -> round to nearest page section
up takes to nearest section


*/