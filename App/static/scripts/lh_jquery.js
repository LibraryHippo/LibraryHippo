var all_tables = ['#info', '#items_due', '#items_not_due', '#holds_ready', '#holds_not_ready'];

function refresh_table_count(section)
{
   var count = $(section + ' tbody tr').length;
   //alert('count = ' + count);
   var replacement_text = count + ' Thing';
   if ( count != 1 )
   {
      replacement_text += 's';
   }
   //alert ('replacement_text = ' + replacement_text);

   var header = $(section + ' h2').text();
   //alert('header = ' + header);
   header = header.replace(/^(\d+) (Things?)/, replacement_text);
   //alert('header = ' + header);
   $(section + ' h2').text(header);
}

function make_error_callback(card_key, attempt_number)
{
   var max_attempts = 3
   return function(request, status, error)
   {
      if ( attempt_number == max_attempts )
      {
         var progress_row = $('#progress tr#' + card_key);
         progress_row.appendTo($('#info tbody'));
         $('td#throbber', progress_row).remove();
         $('td#message', progress_row).html('Unable to check card. <a href="/about#check_failed">Why?</a>');


         refresh_table_count('#info');
         $('#info').show('slow');

         if ( ! $('#progress tr').length )
         {
            $('#progress').hide('slow');
         }
      }
      else
      {
         attempt_number = attempt_number + 1;
         $('#progress tr#' + card_key + " td#message").html('(attempt ' + attempt_number + ' of ' + max_attempts + ')');
         var next_url = '/checkcard/' + card_key;
         $.ajax({
            url: next_url,
            async: true,
            success: make_success_callback(card_key),
            error: make_error_callback(card_key, attempt_number)
         });
      }
   }
}

function make_success_callback(card_key)
{
   return function(data)
   {
      for ( var index in all_tables )
      {              
         var table = all_tables[index];
         var new_rows = $(table + " tbody tr", data);

         new_rows.appendTo($(table + " tbody"));
         $(table + " tbody tr").sort(function(a, b) 
           {
              var key_a = $('.sortkey', a).text();
              var key_b = $('.sortkey', b).text();
              return key_a < key_b ? -1: 1;
           }).appendTo($(table + " tbody")).show('slow');
         refresh_table_count(table);

         if ( $(table + " tbody tr").length )
         {
             $(table).show('slow');
         }
      }

      $('#progress tr#' + card_key).remove();
      if ( ! $('#progress tr').length )
      {
         $('#progress').hide('slow');
         var any_content = false;
         for ( var index in all_tables )
         {              
            var table = all_tables[index];
            any_content |= $(table + " tbody tr").length;
         }
         if ( ! any_content )
         {
            $('#info tbody').append($('<tr><td colspan="3">You have no items out, and no holds. No wonder the world\'s in the shape it is &mdash; nobody reads anymore.</td></tr>'));
            refresh_table_count('#info');
            $('#info').show('slow');
         }
      }
   }
}

function check_cards(card_keys)
{
   if ( ! card_keys.length )
   {
      make_success_callback('no key')('');
   }

   while ( card_keys.length )
   {
      var card_key = card_keys.shift();
      var next_url = '/checkcard/' + card_key;
      
      $.ajax({
           url: next_url,
           async: true,
           success: make_success_callback(card_key),
           error: make_error_callback(card_key, 1)
      });
   }
}

