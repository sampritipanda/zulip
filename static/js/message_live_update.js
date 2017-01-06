var message_live_update = (function () {

var exports = {};

exports.update_stream_name = function (stream_id, new_name) {
    _.each([home_msg_list, current_msg_list, message_list.all], function (list) {
        list.update_stream_name(stream_id, new_name);
    });
};

return exports;

}());
if (typeof module !== 'undefined') {
    module.exports = message_live_update;
}

