/**
 * Acquire Javascript Library. This provides some native JS classes
 * that match the API of the Acquire.Client Python library. This
 * is a client-only library, so only provides matching classes
 * for (some) of the classes available in Acquire.Client
 */

async function test_acquire()
{
    var privkey = new PrivateKey();
    var pubkey = await privkey.public_key();
    console.log(`keys = ${privkey}, ${pubkey}`);

    var e = await pubkey.encrypt("Hello World");
    console.log(`encrypted = ${e}`);
    var m = await privkey.decrypt(e);
    console.log(`decrypted = ${m}`);

    var data = {'bytes': 'LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF1MGp0TmtXN2VMeklUOFMyS1lQMAplWkhRTFpMNXowWUNGRlc1MkJZUkg5cTdFTW5lZ2ZaRmVFZEl0Nk5OQm8za3JTOE9KOWozSjc3eXJUM0hLQ3Y2CmFVNnhydm15R3l4SmIwN2pIYkhLOFdZZitVODdxcXEvVmNlckVCeWtkR1RtRjBRQ2ZDVjNlZ3ZiZThzeVdZcisKcGFqTytTSktUanRFdDdkaDlGaWZBYXZNR0RsaWl6MkV3Mzk1NGxGRzM1b0VlSmk2TDZubkQ0VVNWdVdYRWQzLwpQdDVucitkbENnZlNJRXpHRytFWGlsTUs4NDV4YUlMZXVyRFhlUm9vTDI5M2xrRjNEa0NEUDdGempSem9ST1VvCkYxN0NJbUpzT3o0dmc5OUpBV1Zwa0p6U2RQd0ZBWS82bGxJOVErZlZkRC9WaUlGa0VtWTROVGJGM0V1VXhnZ04KZndJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=='};

    var pubkey2 = await PublicKey.from_data(data);
    data = await pubkey2.to_data();
    console.log(`data = ${data.bytes}`);
    e = await pubkey2.encrypt("Hello World");
    console.log(`BYTES encrypted = ${e}`);
    e = bytes_to_string(e);
    console.log(`STR encrypted = ${e}`);

    e = await pubkey2.to_data();
    console.log(`pubkey2 = ${e}`);
    console.log(JSON.stringify(e));

    service_url = root_server["a0-a0"]["service_url"];
    console.log(service_url);

    var response = await call_function({service_url: service_url});

    console.log(response);

    var s = await Service.from_data(response["service_info"]);
    console.log(s);

    var key = s.public_key();
    e = await key.encrypt("Hello World");
    console.log(`encrypted == ${e}`);

    var data = await s.to_data();
    console.log(data);
    console.log(s.registry_uid());
    var s2 = await Service.from_data(data);
    console.log(s2);
}
