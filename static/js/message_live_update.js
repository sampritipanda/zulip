var message_live_update = (function () {

var exports = {};

exports.update_stream_name = function (stream_id, new_name) {
    _.each([home_msg_list, current_msg_list, message_list.all], function (list) {
        list.update_stream_name(stream_id, new_name);
    });
};

exports.update_avatar = function (person) {
    var sent_by_me = people.is_my_user_id(person.user_id);
    var url = person.avatar_url;
    url = people.format_small_avatar_url(url, sent_by_me);

    $(".inline_profile_picture.u-" + person.user_id).css({
      "background-image": "url(" + url + ")",
    });
};

return exports;

}());
if (typeof module !== 'undefined') {
    module.exports = message_live_update;
}

